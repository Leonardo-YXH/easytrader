# -*- coding:utf-8 -*-
"""
@author:leonardo
@file: np_pymysql_encoder.py
@time: 2019/12/31
 ┌──┐  ┌──┬──┬──┬──┐  ┌──┬──┬──┬──┐  ┌──┬──┬──┬──┐  ┌──┬──┬──┐
 │Esc │  │ F1 │ F2 │ F3 │ F4 │  │ F5 │ F6 │ F7 │ F8 │  │ F9 │F10 │F11 │F12 │  │P/S │S L │P/B│  ┌┐    ┌┐    ┌┐
 └──┘  └──┴──┴──┴──┘  └──┴──┴──┴──┘  └──┴──┴──┴──┘  └──┴──┴──┘ └┘    └┘    └┘
 ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬─────┐  ┌──┬──┬──┐ ┌──┬──┬──┬──┐
 │~ ` │! 1 │@ 2 │# 3 │$ 4 │% 5 │^ 6 │& 7 │* 8 │( 9 │) 0 │_ - │+ = │  BacSp   │  │Ins │Hom │PUp │ │ N L│  / │ *  │ -  │
 ├──┴─┬┴─┬┴─┬┴─┬┴──┴─┬┴─┬┴─┬┴─┬┴─┬┴─┬┴─┬┴─┬───┤  ├──┼──┼──┤ ├──┼──┼──┼──┤
 │ Tab  │ Q  │ W  │ E  │ R  │ T  │ Y  │ U  │ I  │ O  │ P  │{ [ │} ] │  | \   │  │Del │End │PDn │ │ 7  │ 8  │ 9  │    │
 ├─────┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬─┘  └──┴──┴──┘ ├──┼──┼──┤ +  │
 │   Caps   │ A  │ S  │ D  │ F  │ G  │ H  │ J  │ K  │ L  │: ; │" ' │  Enter   │                       │ 4  │ 5  │ 6  │    │
 ├──────┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┤        ┌──┐       ├──┼──┼──┼──┤
 │   Shift    │ Z  │ X  │ C  │ V  │ B  │ N  │ M  │< , │> . │? / │    Shift     │        │ ↑ │       │ 1  │ 2  │ 3  │    │
 ├─────┬──┴─┬─┴──┬┴───┴───┴───┴───┴───┴──┬┴───┐  ┌───┴────┐ ├──┴──┴──┤ E  │
 │   Ctrl   │     │Alt  │             Space             │  Alt  │    │    │ Ctrl│ │  │ ← │ ↓ │ → │ │    0     │  . │←┘│
 └─────┴────┴────┴───────────────────────┴────┘  └──┴──┴──┘ └─────┴──┴──┘
"""

from sqlalchemy import event
import numpy as np


def add_own_encoders(conn, cursor, query, *args):
    cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
    cursor.connection.encoders[np.int32] = lambda value, encoders: int(value)



def enable_np_encoder(engine):
    """
    py_mysql支持np.float64 translate
    :param engine:
    :return:
    """
    event.listen(engine, "before_cursor_execute", add_own_encoders)
