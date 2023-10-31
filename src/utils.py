import os
from typing import Any


def load_all_sprites(sprites: dict[str, dict[str, Any]]) -> None:
    for _, sprites_val in sprites.items():
        if not sprites_val['path'].exists():
            raise FileNotFoundError(sprites_val['path'])
        for _, _, filenames in os.walk(sprites_val['path']):
            for filename in filenames:
                fn, _ = filename.split('.')
                file_ = sprites_val['path'].joinpath(filename)
                if file_.exists() and file_.is_file():
                    with open(file_, mode='r', encoding='utf-8') as frame:
                        sprites_val['sprites'][fn] = frame.read()
