root@iZ0xia1zt60748aekrxmwyZ:~/WB# docker compose ps
NAME            IMAGE                COMMAND                  SERVICE    CREATED          STATUS                          PORTS
wb-backend-1    wb-backend           "sh -c 'alembic upgr…"   backend    14 minutes ago   Restarting (1) 44 seconds ago   
wb-db-1         postgres:15-alpine   "docker-entrypoint.s…"   db         7 hours ago      Up 5 hours (healthy)            0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
wb-frontend-1   wb-frontend          "/docker-entrypoint.…"   frontend   42 minutes ago   Up 42 minutes                   0.0.0.0:1235->80/tcp, [::]:1235->80/tcp

root@iZ0xia1zt60748aekrxmwyZ:~/WB# docker compose logs backend --timestamps --tail=300
backend-1  | 2026-02-11T12:37:51.832949120Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:37:51.832953752Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:37:51.832958860Z     from app.models.account import Account
backend-1  | 2026-02-11T12:37:51.832963183Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:37:51.832967882Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:37:51.832987509Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:38:53.195441140Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:38:53.197288826Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:38:53.197347144Z     sys.exit(main())
backend-1  | 2026-02-11T12:38:53.197352006Z              ~~~~^^
backend-1  | 2026-02-11T12:38:53.197355606Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:38:53.197359955Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:38:53.197363536Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197367358Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:38:53.197371158Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:38:53.197374734Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197378215Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:38:53.197381593Z     fn(
backend-1  | 2026-02-11T12:38:53.197384987Z     ~~^
backend-1  | 2026-02-11T12:38:53.197388119Z         config,
backend-1  | 2026-02-11T12:38:53.197391853Z         ^^^^^^^
backend-1  | 2026-02-11T12:38:53.197395112Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:38:53.197401480Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197405648Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:38:53.197411129Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197416528Z     )
backend-1  | 2026-02-11T12:38:53.197421209Z     ^
backend-1  | 2026-02-11T12:38:53.197426542Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:38:53.197431406Z     script.run_env()
backend-1  | 2026-02-11T12:38:53.197436577Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:38:53.197440435Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:38:53.197445602Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:38:53.197450964Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197455501Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:38:53.197460476Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:38:53.197531804Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:38:53.197536770Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:38:53.197541167Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197545557Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:38:53.197551235Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:38:53.197556090Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:38:53.197561044Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:38:53.197565767Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:38:53.197570597Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:38:53.197575155Z     from app.models.account import Account
backend-1  | 2026-02-11T12:38:53.197579664Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:38:53.197584846Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:38:53.197809391Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:39:54.585482783Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:39:54.588886155Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:39:54.588966982Z     sys.exit(main())
backend-1  | 2026-02-11T12:39:54.588975802Z              ~~~~^^
backend-1  | 2026-02-11T12:39:54.588980856Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:39:54.588986633Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:39:54.588992456Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589001053Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:39:54.589006911Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:39:54.589011969Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589016731Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:39:54.589022156Z     fn(
backend-1  | 2026-02-11T12:39:54.589027203Z     ~~^
backend-1  | 2026-02-11T12:39:54.589032443Z         config,
backend-1  | 2026-02-11T12:39:54.589036388Z         ^^^^^^^
backend-1  | 2026-02-11T12:39:54.589040605Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:39:54.589046018Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589050522Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:39:54.589055385Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589102277Z     )
backend-1  | 2026-02-11T12:39:54.589148495Z     ^
backend-1  | 2026-02-11T12:39:54.589153929Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:39:54.589158750Z     script.run_env()
backend-1  | 2026-02-11T12:39:54.589163099Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:39:54.589167679Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:39:54.589172593Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:39:54.589178079Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589191431Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:39:54.589199237Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:39:54.589203928Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:39:54.589208711Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:39:54.589213627Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589218115Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:39:54.589223262Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:39:54.589228233Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:39:54.589233041Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:39:54.589237278Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:39:54.589241773Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:39:54.589246546Z     from app.models.account import Account
backend-1  | 2026-02-11T12:39:54.589251280Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:39:54.589256193Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:39:54.589263050Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:40:56.053238591Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:40:56.055031884Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:40:56.055131511Z     sys.exit(main())
backend-1  | 2026-02-11T12:40:56.055136887Z              ~~~~^^
backend-1  | 2026-02-11T12:40:56.055140750Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:40:56.055144469Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:40:56.055148238Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055151904Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:40:56.055155627Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:40:56.055159076Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055216481Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:40:56.055221170Z     fn(
backend-1  | 2026-02-11T12:40:56.055225872Z     ~~^
backend-1  | 2026-02-11T12:40:56.055230747Z         config,
backend-1  | 2026-02-11T12:40:56.055235952Z         ^^^^^^^
backend-1  | 2026-02-11T12:40:56.055241693Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:40:56.055247558Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055252816Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:40:56.055258733Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055264053Z     )
backend-1  | 2026-02-11T12:40:56.055268915Z     ^
backend-1  | 2026-02-11T12:40:56.055273219Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:40:56.055281814Z     script.run_env()
backend-1  | 2026-02-11T12:40:56.055287138Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:40:56.055291447Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:40:56.055296434Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:40:56.055301193Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055305484Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:40:56.055310526Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:40:56.055315468Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:40:56.055320564Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:40:56.055325363Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055329979Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:40:56.055334919Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:40:56.055339964Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:40:56.055345083Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:40:56.055350067Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:40:56.055355104Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:40:56.055360149Z     from app.models.account import Account
backend-1  | 2026-02-11T12:40:56.055365222Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:40:56.055370342Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:40:56.055381431Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:41:57.516690177Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:41:57.518745532Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:41:57.518803404Z     sys.exit(main())
backend-1  | 2026-02-11T12:41:57.518808358Z              ~~~~^^
backend-1  | 2026-02-11T12:41:57.518811968Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:41:57.518815582Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:41:57.518819098Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518823045Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:41:57.518826895Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:41:57.518830379Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518833833Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:41:57.518837748Z     fn(
backend-1  | 2026-02-11T12:41:57.518841334Z     ~~^
backend-1  | 2026-02-11T12:41:57.518845212Z         config,
backend-1  | 2026-02-11T12:41:57.518849026Z         ^^^^^^^
backend-1  | 2026-02-11T12:41:57.518852875Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:41:57.518859108Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518863094Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:41:57.518867137Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518871105Z     )
backend-1  | 2026-02-11T12:41:57.518874750Z     ^
backend-1  | 2026-02-11T12:41:57.518878300Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:41:57.518882157Z     script.run_env()
backend-1  | 2026-02-11T12:41:57.518885866Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:41:57.518889228Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:41:57.518893262Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:41:57.518897026Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518900577Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:41:57.518904219Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:41:57.518907431Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:41:57.518911086Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:41:57.518914953Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518918642Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:41:57.518923114Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:41:57.518927429Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:41:57.518972232Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:41:57.518975925Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:41:57.518979144Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:41:57.518983009Z     from app.models.account import Account
backend-1  | 2026-02-11T12:41:57.519059980Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:41:57.519066447Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:41:57.519072832Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:42:58.898127244Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:42:58.899854806Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:42:58.899906521Z     sys.exit(main())
backend-1  | 2026-02-11T12:42:58.899911556Z              ~~~~^^
backend-1  | 2026-02-11T12:42:58.899915131Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:42:58.899918788Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:42:58.899922354Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.899926216Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:42:58.899930146Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:42:58.899933585Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.899937190Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:42:58.899940650Z     fn(
backend-1  | 2026-02-11T12:42:58.899944061Z     ~~^
backend-1  | 2026-02-11T12:42:58.899948604Z         config,
backend-1  | 2026-02-11T12:42:58.899952537Z         ^^^^^^^
backend-1  | 2026-02-11T12:42:58.899955834Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:42:58.899959593Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.899963015Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:42:58.899966801Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.899970460Z     )
backend-1  | 2026-02-11T12:42:58.899973937Z     ^
backend-1  | 2026-02-11T12:42:58.899979916Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:42:58.899983499Z     script.run_env()
backend-1  | 2026-02-11T12:42:58.899986954Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:42:58.899990723Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:42:58.899994511Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:42:58.900033485Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.900038539Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:42:58.900105878Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:42:58.900111376Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:42:58.900117381Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:42:58.900122878Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:42:58.900127986Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:42:58.900133700Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:42:58.900139134Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:42:58.900144505Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:42:58.900149518Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:42:58.900154147Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:42:58.900159859Z     from app.models.account import Account
backend-1  | 2026-02-11T12:42:58.900165024Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:42:58.900169558Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:42:58.900391881Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:44:00.293035928Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:44:00.294730214Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:44:00.294783596Z     sys.exit(main())
backend-1  | 2026-02-11T12:44:00.294788580Z              ~~~~^^
backend-1  | 2026-02-11T12:44:00.294792504Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:44:00.294796017Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:44:00.294799360Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.294803132Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:44:00.294806879Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:44:00.294810539Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.294817570Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:44:00.294822861Z     fn(
backend-1  | 2026-02-11T12:44:00.294828495Z     ~~^
backend-1  | 2026-02-11T12:44:00.294833121Z         config,
backend-1  | 2026-02-11T12:44:00.294844436Z         ^^^^^^^
backend-1  | 2026-02-11T12:44:00.294849860Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:44:00.294855025Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.294859756Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:44:00.294927899Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.294933257Z     )
backend-1  | 2026-02-11T12:44:00.294938033Z     ^
backend-1  | 2026-02-11T12:44:00.294944340Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:44:00.294949112Z     script.run_env()
backend-1  | 2026-02-11T12:44:00.294952990Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:44:00.294957024Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:44:00.294961967Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:44:00.294967523Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.294972359Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:44:00.295025781Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:44:00.295030807Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:44:00.295035884Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:44:00.295041426Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:44:00.295046302Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:44:00.295052140Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:44:00.295056161Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:44:00.295061404Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:44:00.295065799Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:44:00.295070948Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:44:00.295076114Z     from app.models.account import Account
backend-1  | 2026-02-11T12:44:00.295080767Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:44:00.295085249Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:44:00.295092546Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)
backend-1  | 2026-02-11T12:45:01.672801202Z Traceback (most recent call last):
backend-1  | 2026-02-11T12:45:01.674655661Z   File "/usr/local/bin/alembic", line 7, in <module>
backend-1  | 2026-02-11T12:45:01.674757246Z     sys.exit(main())
backend-1  | 2026-02-11T12:45:01.674766742Z              ~~~~^^
backend-1  | 2026-02-11T12:45:01.674772999Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 636, in main
backend-1  | 2026-02-11T12:45:01.674777600Z     CommandLine(prog=prog).main(argv=argv)
backend-1  | 2026-02-11T12:45:01.674782349Z     ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.674786932Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 626, in main
backend-1  | 2026-02-11T12:45:01.674853214Z     self.run_cmd(cfg, options)
backend-1  | 2026-02-11T12:45:01.674857728Z     ~~~~~~~~~~~~^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.674862207Z   File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 603, in run_cmd
backend-1  | 2026-02-11T12:45:01.674866560Z     fn(
backend-1  | 2026-02-11T12:45:01.674870717Z     ~~^
backend-1  | 2026-02-11T12:45:01.674875713Z         config,
backend-1  | 2026-02-11T12:45:01.674880903Z         ^^^^^^^
backend-1  | 2026-02-11T12:45:01.674885347Z         *[getattr(options, k, None) for k in positional],
backend-1  | 2026-02-11T12:45:01.674890308Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.674895360Z         **{k: getattr(options, k, None) for k in kwarg},
backend-1  | 2026-02-11T12:45:01.674911965Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.674919493Z     )
backend-1  | 2026-02-11T12:45:01.674924054Z     ^
backend-1  | 2026-02-11T12:45:01.674928194Z   File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 406, in upgrade
backend-1  | 2026-02-11T12:45:01.674932881Z     script.run_env()
backend-1  | 2026-02-11T12:45:01.674937357Z     ~~~~~~~~~~~~~~^^
backend-1  | 2026-02-11T12:45:01.674941738Z   File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 586, in run_env
backend-1  | 2026-02-11T12:45:01.674946671Z     util.load_python_file(self.dir, "env.py")
backend-1  | 2026-02-11T12:45:01.674951626Z     ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.674955960Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 95, in load_python_file
backend-1  | 2026-02-11T12:45:01.674960342Z     module = load_module_py(module_id, path)
backend-1  | 2026-02-11T12:45:01.674964632Z   File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 113, in load_module_py
backend-1  | 2026-02-11T12:45:01.674969442Z     spec.loader.exec_module(module)  # type: ignore
backend-1  | 2026-02-11T12:45:01.674973795Z     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
backend-1  | 2026-02-11T12:45:01.675029352Z   File "<frozen importlib._bootstrap_external>", line 1023, in exec_module
backend-1  | 2026-02-11T12:45:01.675034469Z   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
backend-1  | 2026-02-11T12:45:01.675039526Z   File "/app/alembic/env.py", line 19, in <module>
backend-1  | 2026-02-11T12:45:01.675044283Z     from app.models import Account, MemberKey, TaskLog  # noqa: F401
backend-1  | 2026-02-11T12:45:01.675048736Z     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend-1  | 2026-02-11T12:45:01.675053386Z   File "/app/app/models/__init__.py", line 3, in <module>
backend-1  | 2026-02-11T12:45:01.675071720Z     from app.models.account import Account
backend-1  | 2026-02-11T12:45:01.675076451Z   File "/app/app/models/account.py", line 6, in <module>
backend-1  | 2026-02-11T12:45:01.675081090Z     from sqlalchemy import relationship
backend-1  | 2026-02-11T12:45:01.675091105Z ImportError: cannot import name 'relationship' from 'sqlalchemy' (/usr/local/lib/python3.13/site-packages/sqlalchemy/__init__.py)