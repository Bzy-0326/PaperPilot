from typing import Dict, Any, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


class GitHubRepoAgent:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def analyze(self, github_url: str) -> Dict[str, Any]:
        if not github_url:
            return self._empty_result()

        repo_name = self._extract_repo_name(github_url)
        repo_url = self._normalize_repo_url(github_url)

        result = {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "repo_exists": False,
            "readme_exists": False,
            "readme_quality": "unknown",
            "setup_instruction_exists": False,
            "train_script_exists": False,
            "infer_script_exists": False,
            "requirements_exists": False,
            "environment_file_exists": False,
            "example_usage_exists": False,
            "checkpoints_or_weights_mentioned": False,
            "reproducibility_level": "low",
            "reproducibility_level_zh": "较难快速复现",
            "repo_summary_text": "未能获取到仓库页面信息。",
            "repo_pros": [],
            "repo_cons": []
        }

        try:
            if not repo_name:
                result["repo_cons"].append("GitHub 仓库链接格式异常")
                return result

            file_names = self._fetch_repo_root_files(repo_name)
            readme_text = self._fetch_readme_text(repo_name)

            if file_names or readme_text:
                result["repo_exists"] = True
            else:
                html_text = self._fetch_repo_html_text(repo_url)
                if html_text:
                    result["repo_exists"] = True
                    self._fill_from_text(result, html_text)

            if file_names:
                self._fill_from_file_names(result, file_names)

            if readme_text:
                result["readme_exists"] = True
                self._fill_from_text(result, readme_text)

            result["readme_quality"] = self._judge_readme_quality(result)
            score = self._calc_score(result)
            result["reproducibility_level"], result["reproducibility_level_zh"] = self._map_level(score)
            result["repo_summary_text"] = self._build_summary(result)
            result["repo_pros"], result["repo_cons"] = self._build_pros_cons(result)

            return result

        except Exception:
            result["repo_cons"].append("仓库分析抓取失败")
            return result

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "repo_url": "",
            "repo_name": "",
            "repo_exists": False,
            "readme_exists": False,
            "readme_quality": "unknown",
            "setup_instruction_exists": False,
            "train_script_exists": False,
            "infer_script_exists": False,
            "requirements_exists": False,
            "environment_file_exists": False,
            "example_usage_exists": False,
            "checkpoints_or_weights_mentioned": False,
            "reproducibility_level": "low",
            "reproducibility_level_zh": "较难快速复现",
            "repo_summary_text": "论文未提供 GitHub 仓库信息。",
            "repo_pros": [],
            "repo_cons": ["未提供 GitHub 仓库"]
        }

    def _extract_repo_name(self, github_url: str) -> str:
        try:
            parsed = urlparse(github_url)
            path = parsed.path.strip("/")
            parts = path.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
            return ""
        except Exception:
            return ""

    def _normalize_repo_url(self, github_url: str) -> str:
        repo_name = self._extract_repo_name(github_url)
        if repo_name:
            return f"https://github.com/{repo_name}"
        return github_url

    def _fetch_repo_root_files(self, repo_name: str) -> List[str]:
        url = f"https://api.github.com/repos/{repo_name}/contents"
        resp = requests.get(url, headers=self.headers, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if not isinstance(data, list):
            return []
        return [item.get("name", "") for item in data if isinstance(item, dict)]

    def _fetch_readme_text(self, repo_name: str) -> str:
        candidates = [
            "README.md",
            "Readme.md",
            "readme.md",
            "README.MD",
        ]
        for name in candidates:
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/HEAD/{name}"
            try:
                resp = requests.get(raw_url, headers=self.headers, timeout=15)
                if resp.status_code == 200 and resp.text.strip():
                    return resp.text.lower()
            except Exception:
                pass
        return ""

    def _fetch_repo_html_text(self, repo_url: str) -> str:
        try:
            resp = requests.get(repo_url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return ""
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup.get_text("\n", strip=True).lower()
        except Exception:
            return ""

    def _fill_from_file_names(self, result: Dict[str, Any], file_names: List[str]) -> None:
        names = [x.lower() for x in file_names]

        if any("readme" in x for x in names):
            result["readme_exists"] = True

        if "requirements.txt" in names:
            result["requirements_exists"] = True

        if any(x in names for x in ["environment.yml", "environment.yaml", "pyproject.toml", "pipfile"]):
            result["environment_file_exists"] = True

        if any(x in names for x in [
            "train.py", "train.sh", "run_train.py", "finetune.py", "main_train.py"
        ]):
            result["train_script_exists"] = True

        if any(x in names for x in [
            "infer.py", "inference.py", "predict.py", "test.py", "eval.py", "demo.py"
        ]):
            result["infer_script_exists"] = True

        if any(x in names for x in ["examples", "example", "demo", "scripts"]):
            result["example_usage_exists"] = True

    def _fill_from_text(self, result: Dict[str, Any], text: str) -> None:
        text = text.lower()

        if "readme" in text:
            result["readme_exists"] = True

        if any(k in text for k in [
            "install", "installation", "setup", "environment", "dependency", "dependencies"
        ]):
            result["setup_instruction_exists"] = True

        if any(k in text for k in [
            "train.py", "train.sh", "training", "run_train", "python train.py", "bash train.sh"
        ]):
            result["train_script_exists"] = True

        if any(k in text for k in [
            "infer.py", "inference", "predict.py", "test.py", "evaluation",
            "demo", "python infer.py", "python predict.py"
        ]):
            result["infer_script_exists"] = True

        if "requirements.txt" in text:
            result["requirements_exists"] = True

        if any(k in text for k in [
            "environment.yml", "environment.yaml", "pyproject.toml", "pipfile", "conda create"
        ]):
            result["environment_file_exists"] = True

        if any(k in text for k in [
            "usage", "example", "examples", "quick start", "quickstart", "how to run"
        ]):
            result["example_usage_exists"] = True

        if any(k in text for k in [
            "checkpoint", "checkpoints", "pretrained", "weights", "model zoo", "huggingface"
        ]):
            result["checkpoints_or_weights_mentioned"] = True

    def _judge_readme_quality(self, result: Dict[str, Any]) -> str:
        count = sum([
            result["setup_instruction_exists"],
            result["train_script_exists"],
            result["infer_script_exists"],
            result["example_usage_exists"],
            result["requirements_exists"] or result["environment_file_exists"],
        ])
        if result["readme_exists"] and count >= 4:
            return "high"
        if result["readme_exists"] and count >= 2:
            return "medium"
        if result["readme_exists"]:
            return "low"
        return "unknown"

    def _calc_score(self, result: Dict[str, Any]) -> int:
        score = 0
        if result["readme_exists"]:
            score += 2
        if result["readme_quality"] == "high":
            score += 2
        elif result["readme_quality"] == "medium":
            score += 1
        if result["setup_instruction_exists"]:
            score += 2
        if result["requirements_exists"] or result["environment_file_exists"]:
            score += 1
        if result["train_script_exists"]:
            score += 2
        if result["infer_script_exists"]:
            score += 2
        if result["example_usage_exists"]:
            score += 1
        if result["checkpoints_or_weights_mentioned"]:
            score += 1
        if not result["readme_exists"]:
            score -= 3
        if not result["train_script_exists"] and not result["infer_script_exists"]:
            score -= 2
        return score

    def _map_level(self, score: int):
        if score >= 7:
            return "high", "较易快速上手复现"
        if score >= 4:
            return "medium", "有一定复现基础，但仍需补充细节"
        return "low", "较难快速复现"

    def _build_summary(self, result: Dict[str, Any]) -> str:
        if not result["repo_exists"]:
            return "仓库链接已识别，但页面不可正常访问。"
        if result["reproducibility_level"] == "high":
            return "仓库说明较完整，包含较多复现相关线索，适合进一步尝试复现。"
        if result["reproducibility_level"] == "medium":
            return "仓库提供了一定复现线索，但仍需补充部分环境或运行细节。"
        return "仓库虽已公开，但可直接用于快速复现的信息仍较有限。"

    def _build_pros_cons(self, result: Dict[str, Any]):
        pros = []
        cons = []

        if result["readme_exists"]:
            pros.append("命中 README")
        else:
            cons.append("缺少 README")

        if result["setup_instruction_exists"]:
            pros.append("包含安装或环境说明")
        else:
            cons.append("安装说明不足")

        if result["train_script_exists"]:
            pros.append("存在训练入口")
        if result["infer_script_exists"]:
            pros.append("存在推理或测试入口")

        if not result["train_script_exists"] and not result["infer_script_exists"]:
            cons.append("缺少明确训练或推理入口")

        if result["requirements_exists"] or result["environment_file_exists"]:
            pros.append("存在依赖环境文件")
        else:
            cons.append("未发现依赖环境文件")

        if result["example_usage_exists"]:
            pros.append("包含示例或脚本目录")

        if result["checkpoints_or_weights_mentioned"]:
            pros.append("提到权重或 checkpoint")

        return pros, cons