# ===== api/pow.py（完整 i18n 版本）=====

from __future__ import annotations

import hashlib

from ..exceptions import PoWError
from ..logging_utils import log_info
from ..i18n import get_text as _


def solve_pow(prefix: str, target_hex: str) -> str:
    """
    按官方说明 + LRCGET 的实现习惯：

    - target 是 16 进制字符串，表示一个 256 位整数阈值
    - 在 nonce 为 0,1,2,... 中寻找第一个满足：
        sha256(prefix + str(nonce)) <= target
    - 返回 nonce 的十进制字符串
    """
    if not prefix or not target_hex:
        raise PoWError(_("无效 PoW 参数：prefix={prefix}, target={target}").format(
            prefix=repr(prefix),
            target=repr(target_hex)
        ))

    target = int(target_hex, 16)

    nonce = 0
    while True:
        token_bytes = (prefix + str(nonce)).encode("utf-8")
        digest = hashlib.sha256(token_bytes).hexdigest()
        if int(digest, 16) <= target:
            log_info(_("找到有效 nonce: {nonce}").format(nonce=nonce))
            return str(nonce)
        nonce += 1
