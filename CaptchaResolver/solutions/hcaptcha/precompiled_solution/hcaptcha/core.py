import os
import re
import typing

from loguru import logger

from ._solutions import resnet, yolo
from .exceptions import ChallengeLangException


class HolyChallenger:
    """hCAPTCHA challenge drive control"""

    _label_alias = {
        "zh": {
            "自行车": "bicycle",
            "火车": "train",
            "卡车": "truck",
            "公交车": "bus",
            "巴士": "bus",
            "飞机": "airplane",
            "一条船": "boat",
            "船": "boat",
            "摩托车": "motorcycle",
            "垂直河流": "vertical river",
            "天空中向左飞行的飞机": "airplane in the sky flying left",
            "请选择天空中所有向右飞行的飞机": "airplanes in the sky that are flying to the right",
            "汽车": "car",
            "大象": "elephant",
            "鸟": "bird",
            "狗": "dog",
            "犬科动物": "dog",
            "一匹马": "horse",
            "长颈鹿": "giraffe",
        },
        "en": {
            "airplane": "airplane",
            "motorbus": "bus",
            "bus": "bus",
            "truck": "truck",
            "motorcycle": "motorcycle",
            "boat": "boat",
            "bicycle": "bicycle",
            "train": "train",
            "vertical river": "vertical river",
            "airplane in the sky flying left": "airplane in the sky flying left",
            "Please select all airplanes in the sky that are flying to the right":
                "airplanes in the sky that are flying to the right",
            "car": "car",
            "elephant": "elephant",
            "bird": "bird",
            "dog": "dog",
            "canine": "dog",
            "horse": "horse",
            "giraffe": "giraffe",
        },
    }

    BAD_CODE = {
        "а": "a",
        "е": "e",
        "e": "e",
        "i": "i",
        "і": "i",
        "ο": "o",
        "с": "c",
        "ԁ": "d",
        "ѕ": "s",
        "һ": "h",
        "у": "y",
        "р": "p",
        "ー": "一",
        "土": "士",
    }

    def __init__(
            self,
            dir_workspace: typing.Optional[str] = None,
            lang: typing.Optional[str] = "zh",
            dir_model: typing.Optional[str] = None,
            onnx_prefix: typing.Optional[str] = None,
            screenshot: typing.Optional[bool] = False,
            debug: typing.Optional[bool] = False,
            path_objects_yaml: typing.Optional[str] = None,
    ):
        if not isinstance(lang, str) or not self._label_alias.get(lang):
            raise ChallengeLangException(
                f"Challenge language [{lang}] not yet supported."
                f" -lang={list(self._label_alias.keys())}"
            )

        self.action_name = "ArmorCaptcha"
        self.dir_model = dir_model or os.path.join("datas", "models")
        self.path_objects_yaml = path_objects_yaml or os.path.join("datas", "objects.yaml")
        self.dir_workspace = dir_workspace or os.path.join("datas", "temp_cache", "_challenge")
        self.debug = debug
        self.onnx_prefix = onnx_prefix
        self.screenshot = screenshot

        # 存储挑战图片的目录
        self.runtime_workspace = ""
        # 挑战截图存储路径
        self.path_screenshot = ""
        # 博大精深！
        self.lang = lang
        self.label_alias: dict = self._label_alias[lang]

        # Store the `element locator` of challenge images {挑战图片1: locator1, ...}
        self.alias2locator = {}
        # Store the `download link` of the challenge image {挑战图片1: url1, ...}
        self.alias2url = {}
        # Store the `directory` of challenge image {挑战图片1: "/images/挑战图片1.png", ...}
        self.alias2path = {}
        # 图像标签
        self.label = ""
        self.prompt = ""

        self.threat = 0

        # Automatic registration
        self.pom_handler = resnet.PluggableONNXModels(
            path_objects_yaml=self.path_objects_yaml, dir_model=self.dir_model, lang=self.lang
        )
        self.label_alias.update(self.pom_handler.label_alias)

    def log(
            self, message: str, _reporter: typing.Optional[bool] = False, **params
    ) -> typing.Optional[str]:
        """格式化日志信息"""
        if not self.debug:
            return

        motive = "Challenge"
        flag_ = f">> {motive} [{self.action_name}] {message}"
        if params:
            flag_ += " - "
            flag_ += " ".join([f"{i[0]}={i[1]}" for i in params.items()])
        if _reporter is True:
            return flag_
        logger.debug(flag_)

    @staticmethod
    def split_prompt_message(prompt_message: str, lang: str) -> str:
        """Detach label from challenge prompt"""
        if lang.startswith("zh"):
            if "的每" in prompt_message:
                res = re.split(r"[击 的每]", prompt_message)[1]
                return res[2:] if res.startswith("包含") else res
            if "包含" in prompt_message:
                return re.split(r"(包含)|(的图)", prompt_message)[3]
        elif lang.startswith("en"):
            prompt_message = prompt_message.replace(".", "").lower()
            if "containing" in prompt_message:
                return re.split(r"containing a", prompt_message)[-1][1:].strip()
            if "select all" in prompt_message:
                return re.split(r"all (.*) images", prompt_message)[1].strip()
        return prompt_message

    def label_cleaning(self, raw_label: str) -> str:
        """cleaning errors-unicode"""
        clean_label = raw_label
        for c in self.BAD_CODE:
            clean_label = clean_label.replace(c, self.BAD_CODE[c])
        return clean_label

    def switch_solution(self):
        """Optimizing solutions based on different challenge labels"""
        label_alias = self.label_alias.get(self.label)

        # Load ONNX model - ResNet | YOLO
        if label_alias not in self.pom_handler.fingers:
            self.log("lazy-loading", sign="YOLO", match=label_alias)
            return yolo.YOLO(self.dir_model, self.onnx_prefix)
        return self.pom_handler.lazy_loading(label_alias)

    def classify(
            self, prompt: str, images: typing.List[typing.Union[str, bytes]]
    ) -> typing.Optional[typing.List[bool]]:
        """TaskType: HcaptchaClassification"""
        if not prompt or not isinstance(prompt, str) or not images or not isinstance(images, list):
            logger.error("Invalid parameters - " f"prompt=「{self.prompt}」" f"images=「{images}」")
            return

        self.lang = "zh" if re.compile("[\u4e00-\u9fa5]+").search(prompt) else "en"
        self.label_alias = self._label_alias[self.lang]
        self.label_alias.update(self.pom_handler.get_label_alias(self.lang))
        self.prompt = prompt
        _label = self.split_prompt_message(prompt, lang=self.lang)
        self.label = self.label_cleaning(_label)

        if self.label not in self.label_alias:
            logger.error(
                "Types of challenges not yet scheduled - "
                f"label=「{self.label}」 "
                f"prompt=「{self.prompt}」"
            )
            return

        model = self.switch_solution()
        response = []
        for img in images:
            try:
                if isinstance(img, str) and os.path.isfile(img):
                    with open(img, "rb") as file:
                        response.append(
                            model.solution(
                                img_stream=file.read(), label=self.label_alias[self.label]
                            )
                        )
                elif isinstance(img, bytes):
                    response.append(
                        model.solution(img_stream=img, label=self.label_alias[self.label])
                    )
                else:
                    response.append(False)
            except Exception as err:
                logger.exception(err)
                response.append(False)
        return response
