# Run by `frappe-sandbox up` once, right after the sandbox site is copied from preview.localhost.
# Frappe is connected to the sandbox site (frappe.local.site).
#
# The copy points at the same Qdrant alias as preview, so saving a guideline here would rewrite
# preview's semantic index. Give the sandbox its own copy of the index instead: same points and
# vectors (no embedding calls, no cost), under an alias of its own. Candy AI keeps its settings:
# its calls only ask and answer.
import time

import frappe

from candy_wiki.ai.semantic.qdrant import DROPPABLE_PREFIX, QdrantClient
from candy_wiki.ai.semantic.settings import SemanticSettings

settings = SemanticSettings.load()
if not settings.configured:
	print("semantic search isn't configured on the source site; nothing to copy")
else:
	client = QdrantClient(settings)
	source = client.resolve_alias(settings.alias) or settings.alias
	alias = DROPPABLE_PREFIX + frappe.local.site.split(".")[0].replace("-", "_")
	collection = f"{alias}_{int(time.time())}"
	client.create_collection(collection, client.dense_size(source) or settings.dimension)
	copied, offset = 0, None
	while True:
		body = {"limit": 256, "with_payload": True, "with_vector": True}
		if offset is not None:
			body["offset"] = offset
		page = client._request("POST", f"/collections/{source}/points/scroll", json=body)
		points = [
			{"id": p["id"], "vector": p["vector"], "payload": p.get("payload") or {}}
			for p in page.get("points") or []
		]
		client.upsert(collection, points)
		copied += len(points)
		offset = page.get("next_page_offset")
		if offset is None:
			break
	client.point_alias(alias, collection)
	frappe.db.set_single_value("Wiki Settings", "semantic_collection_alias", alias)
	frappe.clear_cache()
	print(f"semantic index: copied {copied} points from {source} to {collection} (alias {alias})")
