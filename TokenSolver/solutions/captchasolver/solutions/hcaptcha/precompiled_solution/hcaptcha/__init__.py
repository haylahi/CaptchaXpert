import typing

from .core import HolyChallenger

__all__ = ["HolyChallenger", "new_challenger", "exceptions"]
__version__ = "0.4.2.25"


def new_challenger(
        host,
        driver,
        hook_frame,
        challenge_frame,
        next_locator=None,
        image_getting_method: str = 'screenshot',
        dir_workspace: str = "_challenge",
        onnx_prefix: typing.Optional[str] = None,
        lang: typing.Optional[str] = "en",
        screenshot: typing.Optional[bool] = False,
        debug: typing.Optional[bool] = False,
) -> HolyChallenger:
    return HolyChallenger(
        host,
        driver,
        hook_frame,
        challenge_frame,
        image_getting_method,
        next_locator,
        dir_workspace=dir_workspace,
        dir_model=None,
        path_objects_yaml=None,
        lang=lang,
        onnx_prefix=onnx_prefix,
        screenshot=screenshot,
        debug=debug,
    )
