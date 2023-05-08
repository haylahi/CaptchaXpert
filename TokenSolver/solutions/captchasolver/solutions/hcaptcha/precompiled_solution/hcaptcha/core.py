import os
import random
import re
import shutil
import time
import typing
from urllib.parse import quote
from urllib.request import getproxies

import requests
from loguru import logger

from .exceptions import LabelNotFoundException, ChallengePassed, ChallengeLangException
from ....common import *


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
            "Please select all airplanes in the sky that are flying to the right": "airplanes in the sky that are flying to the right",
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

    HOOK_CHALLENGE = "//iframe[contains(@title,'content')]"

    # <success> Challenge Passed by following the expected
    CHALLENGE_SUCCESS = "success"
    # <continue> Continue the challenge
    CHALLENGE_CONTINUE = "continue"
    # <crash> Failure of the challenge as expected
    CHALLENGE_CRASH = "crash"
    # <retry> Your proxy IP may have been flagged
    CHALLENGE_RETRY = "retry"
    # <refresh> Skip the specified label as expected
    CHALLENGE_REFRESH = "refresh"
    # <backcall> (New Challenge) Types of challenges not yet scheduled
    CHALLENGE_BACKCALL = "backcall"

    def __init__(
            self,
            host,
            driver,
            hook_frame,
            challenge_frame,
            image_getting_method,
            next_locator,
            dir_workspace: typing.Optional[str] = None,
            lang: typing.Optional[str] = "zh",
            dir_model: typing.Optional[str] = None,
            onnx_prefix: typing.Optional[str] = None,
            screenshot: typing.Optional[bool] = False,
            debug: typing.Optional[bool] = False,
            path_objects_yaml: typing.Optional[str] = None,
    ):
        self.HOST = host
        self.next_locator = next_locator
        self.driver = driver
        self.HOOK_FRAME = hook_frame
        self.CHALLENGE_FRAME = challenge_frame
        self.image_getting_method = image_getting_method
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

    @property
    def utils(self):
        return ArmorUtils

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

    def _init_workspace(self):
        """初始化工作目录，存放缓存的挑战图片"""
        _prefix = (
            f"{time.time()}" + f"_{self.label_alias.get(self.label, '')}" if self.label else ""
        )
        _workspace = os.path.join(self.dir_workspace, _prefix)
        os.makedirs(_workspace, exist_ok=True)
        return _workspace

    def captcha_screenshot(self, ctx, name_screenshot: str = None):
        """
        保存挑战截图，需要在 get_label 之后执行

        :param name_screenshot: filename of the Challenge image
        :param ctx: Webdriver 或 Element
        :return:
        """
        _suffix = self.label_alias.get(self.label, self.label)
        _filename = (
            f"{int(time.time())}.{_suffix}.png" if name_screenshot is None else name_screenshot
        )
        _out_dir = os.path.join(os.path.dirname(self.dir_workspace), "captcha_screenshot")
        _out_path = os.path.join(_out_dir, _filename)
        os.makedirs(_out_dir, exist_ok=True)

        # FullWindow screenshot or FocusElement screenshot
        try:
            ctx.screenshot(_out_path)
        except AttributeError:
            ctx.save_screenshot(_out_path)
        except Exception as err:
            logger.exception(
                self.log(
                    _reporter=True,
                    motive="SCREENSHOT",
                    action_name=self.action_name,
                    message="挑战截图保存失败，错误的参数类型",
                    type=type(ctx),
                    err=err,
                )
            )
        finally:
            return _out_path

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
    def switch_to_challenge_frame(ctx, frame):
        ctx.switch_to.frame(frame)

    def get_label(self, ctx):
        """
        获取人机挑战需要识别的图片类型（标签）

        :param ctx:
        :return:
        """

        # Scan and determine the type of challenge.
        for _ in range(3):
            try:
                label_obj = WebDriverWait(ctx, 30).until(EC.presence_of_element_located((By.XPATH, "//h2[@class='prompt-text']")))
            except TimeoutException:
                raise ChallengePassed("Man-machine challenge unexpectedly passed")
            else:
                self.prompt = label_obj.text
                if self.prompt:
                    break
                time.sleep(1)
                continue
        # Skip the `draw challenge`
        else:
            fn = f"{int(time.time())}.image_label_area_select.png"
            self.log(
                message="Pass challenge",
                challenge="image_label_area_select",
                site_link=ctx.current_url,
                screenshot=self.captcha_screenshot(ctx, fn),
            )
            return self.CHALLENGE_BACKCALL

        # Continue the `click challenge`
        try:
            _label = self.split_prompt_message(prompt_message=self.prompt, lang=self.lang)
        except (AttributeError, IndexError):
            raise LabelNotFoundException("Get the exception label object")
        else:
            self.label = self.label_cleaning(_label)
            self.log(message="Get label", label=f"「{self.label}」")

    def tactical_retreat(self, ctx) -> typing.Optional[str]:
        """
        「blacklist mode」 skip unchoreographed challenges
        :param ctx:
        :return: the screenshot storage path
        """

        if self.label_alias.get(self.label):
            return self.CHALLENGE_CONTINUE

        # Save a screenshot of the challenge
        try:
            challenge_container = ctx.find_element(By.XPATH, "//body[@class='no-selection']")
            self.path_screenshot = self.captcha_screenshot(challenge_container)
        except NoSuchElementException:
            pass
        except WebDriverException as err:
            logger.exception(err)
        finally:
            q = quote(self.label, "utf8")
            logger.warning(
                self.log(
                    _reporter=True,
                    motive="ALERT",
                    action_name=self.action_name,
                    message="Types of challenges not yet scheduled",
                    label=f"「{self.label}」",
                    prompt=f"「{self.prompt}」",
                    screenshot=self.path_screenshot,
                    site_link=ctx.current_url,
                    issues=f"https://github.com/QIN2DIM/hcaptcha-challenger/issues?q={q}",
                )
            )
            return self.CHALLENGE_BACKCALL

    def mark_samples(self, ctx):
        """
        Get the download link and locator of each challenge image

        :param ctx:
        :return:
        """
        # 等待图片加载完成
        try:
            WebDriverWait(ctx, 5, ignored_exceptions=(ElementNotVisibleException,)).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='task-image']"))
            )
        except TimeoutException:
            try:
                ctx.switch_to.default_content()
                WebDriverWait(ctx, 1, 0.1).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//div[contains(@class,'hcaptcha-success')]")
                    )
                )
                return self.CHALLENGE_SUCCESS
            except WebDriverException:
                try:
                    if callable(self.next_locator):
                        raise TimeoutException
                    WebDriverWait(ctx, 1, 0.1).until(
                        EC.visibility_of_element_located(
                            self.next_locator
                        )
                    )
                    return self.CHALLENGE_SUCCESS
                except TimeoutException:
                    return self.CHALLENGE_CONTINUE

        time.sleep(0.3)

        # DOM 定位元素
        samples = ctx.find_elements(By.XPATH, "//div[@class='task-image']")
        for sample in samples:
            alias = sample.get_attribute("aria-label")
            while True:
                try:
                    image_style = sample.find_element(By.CLASS_NAME, "image").get_attribute("style")
                    url = re.split(r'[(")]', image_style)[2]
                    self.alias2url.update({alias: url})
                    break
                except IndexError:
                    continue
            self.alias2locator.update({alias: sample})

    def download_images(self):
        """
        Download Challenge Image

        ### hcaptcha has a challenge duration limit

        If the page element is not manipulated for a period of time,
        the <iframe> box will disappear and the previously acquired Element Locator will be out of date.
        Need to use some modern methods to shorten the time of `getting the dataset` as much as possible.

        ### Solution

        1. Coroutine Downloader
          Use the coroutine-based method to _pull the image to the local, the best practice (this method).
          In the case of poor network, _pull efficiency is at least 10 times faster than traversal download.

        2. Screen cut
          There is some difficulty in coding.
          Directly intercept nine pictures of the target area, and use the tool function to cut and identify them.
          Need to weave the locator index yourself.

        :return:
        """

        # Initialize the challenge image download directory
        self.runtime_workspace = self._init_workspace()

        # Initialize the data container
        docker_ = []
        for alias_, url_ in self.alias2url.items():
            path_challenge_img_ = os.path.join(self.runtime_workspace, f"{alias_}.png")
            self.alias2path.update({alias_: path_challenge_img_})
            docker_.append((path_challenge_img_, url_))

        for url, path in zip(self.alias2url.values(), self.alias2path.values()):
            with open(path, 'wb') as f:
                f.write(requests.get(url).content)

    def get_images_as_base64(self):
        if self.image_getting_method == 'screenshot':
            try:
                imgs = [loc.screenshot_as_base64 for loc in self.alias2locator.values()]
            except ElementClickInterceptedException:
                self.download_images()
                imgs = [path_to_base64(self.alias2path[alias], encoding='ascii') for alias in self.alias2path]
        else:
            self.download_images()
            imgs = [path_to_base64(self.alias2path[alias], encoding='ascii') for alias in self.alias2path]
        return imgs

    def challenge(self, ctx):
        """
        图像分类，元素点击，答案提交

        ### 性能瓶颈

        此部分图像分类基于 CPU 运行。如果服务器资源极其紧张，图像分类任务可能无法按时完成。
        根据实验结论来看，如果运行时内存少于 512MB，且仅有一个逻辑线程的话，基本上是与深度学习无缘了。

        ### 优雅永不过时

        `hCaptcha` 的挑战难度与 `reCaptcha v2` 不在一个级别。
        这里只要正确率上去就行，也即正确图片覆盖更多，通过率越高（即使因此多点了几个干扰项也无妨）。
        所以这里要将置信度尽可能地调低（未经针对训练的模型本来就是用来猜的）。

        :return:
        """

        ta = []
        # {{< IMAGE CLASSIFICATION >}}
        imgs = self.get_images_as_base64()
        data = {'type': 'hcaptcha', 'images': imgs, 'prompt': self.prompt}
        response = requests.post(f'{self.HOST}/resolve', json=data)
        results = response.json()['response']

        # Pass: Hit at least one object
        if results:
            mapped_result = list(zip(results, self.alias2locator))
            random.shuffle(mapped_result)
            for result, alias in mapped_result:
                if result:
                    try:
                        time.sleep(random.uniform(0.1, 1.0))
                        elm = self.alias2locator[alias]
                        ctx.execute_script("arguments[0].click()", elm)
                    except StaleElementReferenceException:
                        pass
                    except WebDriverException as err:
                        logger.warning(err)

        time.sleep(random.uniform(1.0, 2.0))
        # {{< SUBMIT ANSWER >}}
        try:
            elm = WebDriverWait(ctx, 15, ignored_exceptions=(ElementClickInterceptedException,)).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='button-submit button']"))
            )
            ctx.execute_script("arguments[0].click()", elm)
        except ElementClickInterceptedException:
            pass
        except WebDriverException as err:
            logger.exception(err)

    def challenge_success(self, ctx) -> typing.Tuple[str, str]:
        """
        判断挑战是否成功的复杂逻辑

        # 首轮测试后判断短时间内页内是否存在可点击的拼图元素
        # hcaptcha 最多两轮验证，一般情况下，账号信息有误仅会执行一轮，然后返回登录窗格提示密码错误
        # 其次是被识别为自动化控制，这种情况也是仅执行一轮，回到登录窗格提示“返回数据错误”

        经过首轮识别点击后，出现四种结果:
            1. 直接通过验证（小概率）
            2. 进入第二轮（正常情况）
                通过短时间内可否继续点击拼图来断言是否陷入第二轮测试
            3. 要求重试（小概率）
                特征被识别|网络波动|被标记的（代理）IP
            4. 通过验证，弹出 2FA 双重认证
              无法处理，任务结束

        :param ctx: 挑战者驱动上下文
        :return:
        """

        def is_challenge_image_clickable():
            try:
                WebDriverWait(ctx, 1, poll_frequency=0.1).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='task-image']"))
                )
                return True
            except TimeoutException:
                return False

        def is_flagged_flow():
            try:
                WebDriverWait(ctx, 1.2, poll_frequency=0.1).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@class='error-text']"))
                )
                self.threat += 1
                if getproxies() and self.threat > 3:
                    logger.warning(f"Your proxy IP may have been flagged - proxies={getproxies()}")
                return True
            except TimeoutException:
                return False

        time.sleep(1)
        if not callable(self.next_locator):
            if multiWaitNsec(ctx, [is_flagged_flow, is_challenge_image_clickable, self.next_locator], 3, 30) == 2:
                return self.CHALLENGE_SUCCESS, '_'
        if is_flagged_flow():
            return self.CHALLENGE_RETRY, "重置挑战"
        if is_challenge_image_clickable():
            return self.CHALLENGE_CONTINUE, "继续挑战"
        return self.CHALLENGE_SUCCESS, "退火成功"

    def anti_checkbox(self, ctx):
        """处理复选框"""
        try:
            # [👻] 进入复选框
            WebDriverWait(ctx, 30, ignored_exceptions=(ElementNotVisibleException,)).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[contains(@title,'checkbox')]")
                )
            )
            # [👻] 点击复选框
            elm = WebDriverWait(ctx, 30).until(EC.presence_of_element_located((By.ID, "checkbox")))
            ctx.execute_script("arguments[0].click()", elm)
            self.log("Handle hCaptcha checkbox")
            return True
        except (TimeoutException, InvalidArgumentException):
            pass
        finally:
            # [👻] 回到主线剧情
            ctx.switch_to.default_content()

    def anti_hcaptcha(self) -> typing.Union[bool, str]:
        """
        Handle hcaptcha challenge

        ## Method

        具体思路是：
        1. 进入 hcaptcha iframe
        2. 获取图像标签
            需要加入判断，有时候 `hcaptcha` 计算的威胁程度极低，会直接让你过，
            于是图像标签之类的元素都不会加载在网页上。
        3. 获取各个挑战图片的下载链接及网页元素位置
        4. 图片下载，分类
            需要用一些技术手段缩短这部分操作的耗时。人机挑战有时间限制。
        5. 对正确的图片进行点击
        6. 提交答案
        7. 判断挑战是否成功
            一般情况下 `hcaptcha` 的验证有两轮，
            而 `recaptcha vc2` 之类的人机挑战就说不准了，可能程序一晚上都在“循环”。

        ## Reference

        M. I. Hossen and X. Hei, "A Low-Cost Attack against the hCaptcha System," 2021 IEEE Security
        and Privacy Workshops (SPW), 2021, pp. 422-431, doi: 10.1109/SPW53761.2021.00061.

        > ps:该篇文章中的部分内容已过时，如今的 hcaptcha challenge 远没有作者说的那么容易应付。
        :return:
        """
        ctx = self.driver

        # [👻] 它來了！
        try:
            for index in range(3):
                # [👻] 進入挑戰框架
                HolyChallenger.switch_to_challenge_frame(ctx, self.CHALLENGE_FRAME)

                # [👻] 獲取挑戰標簽
                if drop := self.get_label(ctx) in [self.CHALLENGE_BACKCALL]:
                    ctx.switch_to.default_content()
                    return drop

                # [👻] 編排定位器索引
                if drop := self.mark_samples(ctx) in [
                    self.CHALLENGE_SUCCESS,
                    self.CHALLENGE_CONTINUE,
                ]:
                    ctx.switch_to.default_content()
                    return drop

                # [👻] 拉取挑戰圖片
                self.challenge(ctx)

                # [👻] 輪詢控制臺響應
                result, _ = self.challenge_success(ctx)
                self.log("Get response", desc=result)

                ctx.switch_to.default_content()
                shutil.rmtree(self.runtime_workspace, ignore_errors=True)

                if result in [self.CHALLENGE_SUCCESS, self.CHALLENGE_CRASH, self.CHALLENGE_RETRY]:
                    return result

        except WebDriverException as err:
            logger.exception(err)
            ctx.switch_to.default_content()
            return self.CHALLENGE_CRASH

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


class ArmorUtils:
    @staticmethod
    def face_the_checkbox(ctx) -> typing.Optional[bool]:
        try:
            WebDriverWait(ctx, 30, ignored_exceptions=(WebDriverException,)).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'checkbox')]"))
            )
            return True
        except TimeoutException:
            return False

    @staticmethod
    def get_hcaptcha_response(ctx) -> bool:
        try:
            return ctx.execute_script(
                '''return document.querySelector('[title*="checkbox for hCaptcha"]').getAttribute('data-hcaptcha-response')''')
        except:
            return False

    @staticmethod
    def refresh(ctx) -> typing.Optional[bool]:
        try:
            elm = ctx.find_element(By.XPATH, "//div[@class='refresh button']")
            ctx.execute_script("arguments[0].click()", elm)
        except (NoSuchElementException, ElementNotInteractableException):
            return False
        return True
