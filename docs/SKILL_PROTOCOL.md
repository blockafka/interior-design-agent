# Skill 协议（给写 skill_loader 的人看）

> 本文档定义 B3「真 Skill 化」的运行时约定。任何对本协议的修改必须群内同步。

---

## 0. 总览

每个 Agent = 一个 `core/agents/<name>/` 目录，至少包含：

```
core/agents/<name>/
├── SKILL.md          # 元数据 + 文档（YAML frontmatter + Markdown 正文）
├── agent.py          # 实现（必须 export `async def run(...)`）
└── __init__.py       # 空文件
```

`skill_loader.py` 的工作：扫描所有 `core/agents/*/SKILL.md`，解析 frontmatter，按 `order` 排序，动态 import 对应 `agent.py` 的 `run` 函数，返回一个 `list[Skill]` 给 orchestrator 使用。

---

## 1. SKILL.md frontmatter 字段约定

```yaml
---
name: <string>              # 唯一标识，与目录名一致，snake_case
description: <string>       # 一句话职责（≤ 100 字），评委 / 队友看
order: <int>                # 执行顺序，1-5
input_schema: <str>         # core/schemas.py 中的类名（单输入或 "A + B" 表示多输入）
output_schema: <str>        # core/schemas.py 中的类名
tools:                      # 依赖的工具层模块，便于做 import 拓扑分析
  - <string>
  - <string>
owner: <string>             # 负责人（kafka / TBD / ...）
status: <enum>              # skeleton | in_progress | done | live
---
```

**校验规则**：
- `name` 必须等于目录名（loader 启动时 assert）
- `order` 必须在 1-5，且不能重复
- `input_schema` / `output_schema` 必须能从 `core.schemas` 反射出对应 class

---

## 2. agent.py 实现接口约定

每个 `agent.py` **必须**导出一个 async 函数，命名固定为 `run`。

### 单输入 Agent（collector / analyzer / generator）
```python
async def run(input: <InputSchema>) -> <OutputSchema>:
    ...
```

### 多输入 Agent（prompter / copywriter）
```python
async def run(*inputs) -> <OutputSchema>:
    # 通过位置参数接收上游传来的多个对象
    # 顺序由 orchestrator 保证
    ...
```

> 后续可能改为 kwargs 形式，由 loader 根据 SKILL.md 的 input_schema 智能拆解。**当前先用位置参数**。

---

## 3. skill_loader.py 实现伪代码

```python
import importlib
from pathlib import Path
import yaml  # 或 python-frontmatter

from pydantic import BaseModel
from core import schemas

AGENTS_DIR = Path(__file__).parent / "agents"


class Skill(BaseModel):
    name: str
    description: str
    order: int
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    tools: list[str]
    owner: str
    status: str
    run: object  # async callable

    class Config:
        arbitrary_types_allowed = True


def _parse_skill_md(path: Path) -> dict:
    """读 SKILL.md，提取 frontmatter YAML 块"""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path} 缺少 frontmatter"
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm)


def _resolve_schema(name: str) -> type[BaseModel]:
    """input_schema='CollectedContent + UserRequest' → 取第一个"""
    primary = name.split("+")[0].strip()
    return getattr(schemas, primary)


def load_skills() -> list[Skill]:
    skills = []
    for skill_dir in AGENTS_DIR.iterdir():
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        meta = _parse_skill_md(skill_dir / "SKILL.md")
        assert meta["name"] == skill_dir.name

        mod = importlib.import_module(f"core.agents.{skill_dir.name}.agent")
        run_fn = getattr(mod, "run")

        skills.append(Skill(
            name=meta["name"],
            description=meta["description"],
            order=meta["order"],
            input_schema=_resolve_schema(meta["input_schema"]),
            output_schema=_resolve_schema(meta["output_schema"]),
            tools=meta.get("tools", []),
            owner=meta.get("owner", "TBD"),
            status=meta.get("status", "skeleton"),
            run=run_fn,
        ))

    skills.sort(key=lambda s: s.order)
    _validate_chain(skills)
    return skills


def _validate_chain(skills: list[Skill]) -> None:
    """启动时校验：前一个 Agent 的 output_schema 必须能喂给后一个 Agent
    （或为多输入 Agent 的位置参数之一）。
    校验失败立刻 raise，不要等运行时崩。
    """
    # TODO 实现具体的 schema 兼容性检查
    pass
```

---

## 4. orchestrator.py 改造后的形态

```python
from core.skill_loader import load_skills

_skills = load_skills()  # 启动时加载一次

async def run(request: UserRequest) -> FinalPost:
    request_id = str(uuid.uuid4())
    state = {"request": request}  # 用 dict 累积所有中间结果

    for skill in _skills:
        # 根据 skill.input_schema 从 state 里取参数（具体策略由 loader 维护者决定）
        inputs = _select_inputs(state, skill)
        output = await skill.run(*inputs)
        state[skill.output_schema.__name__] = output

    # 组装最终 FinalPost
    return FinalPost(
        request_id=request_id,
        style_dna=state["StyleDNA"],
        images=state["GeneratedImages"],
        copy=state["CopyContent"],
        generated_at=datetime.now(),
    )
```

---

## 5. 当前过渡期实现

`skill_loader.py` 尚未实现，**orchestrator.py 暂时仍用硬编码 import 路径**：
```python
from core.agents.collector.agent import run as collector_run
from core.agents.analyzer.agent import run as analyzer_run
...
```

当前为了在 collector 未接入前跑通后续链路，`orchestrator.run(...)` 已支持两个联调入口：

```python
async def run(
    request: UserRequest,
    collected_content: CollectedContent | None = None,
    collect_dir: str | None = None,
) -> FinalPost:
    ...
```

优先级：

1. `collected_content`：测试代码可直接传标准 `CollectedContent`。
2. `collect_dir`：读取 `data/collect/<账号>` 这类本地采集结果文件夹。
3. 都不传：调用真实 `collector_run(request)`。

skill_loader 实现完成后，把硬编码 import 整体替换为 `_skills = load_skills()` 即可；但要保留上述 collector 旁路能力，方便 demo / 测试在采集 Agent 不稳定时仍能跑完整后 4 步。

---

## 6. 实现 checklist（给负责 loader 的队友）

- [ ] 在 `core/skill_loader.py` 实现 `load_skills()` 函数
- [ ] 在 `core/orchestrator.py` 把硬编码 import 替换为动态加载
- [ ] 在 `tests/` 加 `test_skill_loader.py` 单测（至少覆盖：5 个 Skill 都能加载 / order 不重复 / schema chain 不漂移）
- [ ] 在 `make smoke` 之外加 `make verify-skills`（启动期间只做校验，不真跑 Agent）

完成后通知群里，所有人 `git pull` 验证一遍。
