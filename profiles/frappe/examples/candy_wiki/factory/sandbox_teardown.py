# Run by `frappe-sandbox drop` before the sandbox site is deleted: remove its copy of the
# semantic index. Only names under DROPPABLE_PREFIX can go; preview's index is never touched.
from candy_wiki.ai.semantic.qdrant import DROPPABLE_PREFIX, QdrantClient
from candy_wiki.ai.semantic.settings import SemanticSettings

settings = SemanticSettings.load()
alias = settings.alias
if settings.configured and alias.startswith(DROPPABLE_PREFIX):
	client = QdrantClient(settings)
	names = [c["name"] for c in client._request("GET", "/collections").get("collections") or []]
	client.drop_alias(alias) if client.resolve_alias(alias) else None
	for name in names:
		if name.startswith(alias + "_"):
			client.drop_collection(name)
			print(f"semantic index: dropped {name}")
