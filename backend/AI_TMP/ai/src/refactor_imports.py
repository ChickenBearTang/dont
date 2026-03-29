import os
import re

mapping = {
    r"from consumption_poc\.config": "from config",
    r"import consumption_poc\.config": "import config",

    r"from consumption_poc\.models": "from domain.consumption.schemas",
    r"import consumption_poc\.models": "import domain.consumption.schemas",

    r"from consumption_poc\.service": "from domain.consumption.service",
    r"import consumption_poc\.service": "import domain.consumption.service",

    r"from consumption_poc\.reporting": "from domain.consumption.reporting",
    r"import consumption_poc\.reporting": "import domain.consumption.reporting",

    r"from consumption_poc\.anomaly": "from domain.consumption.anomaly",
    r"import consumption_poc\.anomaly": "import domain.consumption.anomaly",

    r"from consumption_poc\.ai_insights": "from domain.consumption.ai_insights",
    r"import consumption_poc\.ai_insights": "import domain.consumption.ai_insights",

    r"from consumption_poc\.chat_agent": "from domain.chat.chat_agent",
    r"import consumption_poc\.chat_agent": "import domain.chat.chat_agent",

    r"from consumption_poc\.loader": "from utils.loader",
    r"import consumption_poc\.loader": "import utils.loader",

    r"from consumption_poc\.writers": "from utils.writers",
    r"import consumption_poc\.writers": "import utils.writers",

    r"from strict_secretary\.models": "from domain.strict_secretary.models",
    r"import strict_secretary\.models": "import domain.strict_secretary.models",

    r"from strict_secretary\.service": "from domain.strict_secretary.service",
    r"import strict_secretary\.service": "import domain.strict_secretary.service",

    r"from strict_secretary\.voice": "from domain.strict_secretary.voice",
    r"import strict_secretary\.voice": "import domain.strict_secretary.voice",

    r"from strict_secretary\.loader": "from domain.strict_secretary.loader",
    r"import strict_secretary\.loader": "import domain.strict_secretary.loader",

    r"from strict_secretary\.agent": "from domain.strict_secretary.agent",
    r"import strict_secretary\.agent": "import domain.strict_secretary.agent",
}

def update_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for pattern, repl in mapping.items():
        new_content = re.sub(pattern, repl, new_content)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {path}")

for root, dirs, files in os.walk('.'):
    for fn in files:
        if fn.endswith('.py') and fn != 'refactor_imports.py':
            update_file(os.path.join(root, fn))
