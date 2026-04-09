"""Ableton browser traversal and loading helpers."""

from __future__ import absolute_import, print_function, unicode_literals


class BrowserOpsMixin(object):
    """Browser inspection and loading commands."""

    def _get_browser_item_info(self, item, depth=0, max_depth=2):
        info = {
            "name": item.name,
            "uri": item.uri if hasattr(item, "uri") else "",
            "is_device": item.is_device if hasattr(item, "is_device") else False,
            "is_loadable": item.is_loadable if hasattr(item, "is_loadable") else False,
        }
        if depth < max_depth and hasattr(item, "children"):
            children = list(item.children)[:20]
            info["children"] = [self._get_browser_item_info(child, depth + 1, max_depth) for child in children]
        return info

    def _get_browser_tree(self, params):
        category = str(params.get("category_type", "all")).lower()
        roots = self._available_browser_roots()

        if category == "all":
            result = {}
            for key, root in roots.items():
                try:
                    children = list(root.children)[:15]
                    result[key] = [
                        {"name": child.name, "uri": child.uri if hasattr(child, "uri") else ""}
                        for child in children
                    ]
                except Exception:
                    pass
            return result

        root = self._get_browser_root(category)
        return self._get_browser_item_info(root, max_depth=2)

    def _get_browser_items_at_path(self, params):
        path = str(params.get("path", ""))
        parts = [part.strip() for part in path.split("/") if part.strip()]
        top_map = self._available_browser_roots()

        if not parts:
            items = []
            for name, root in top_map.items():
                try:
                    items.append({"name": name, "uri": root.uri if hasattr(root, "uri") else ""})
                except Exception:
                    pass
            return {"items": items, "path": ""}

        current = self._get_browser_root(parts[0])

        for part in parts[1:]:
            found = None
            for child in current.children:
                if child.name.lower() == part.lower():
                    found = child
                    break
            if found is None:
                raise ValueError("Browser path component '{}' not found".format(part))
            current = found

        items = []
        for child in current.children:
            items.append({
                "name": child.name,
                "uri": child.uri if hasattr(child, "uri") else "",
                "is_loadable": child.is_loadable if hasattr(child, "is_loadable") else False,
                "is_device": child.is_device if hasattr(child, "is_device") else False,
            })
        return {"items": items, "path": path}

    def _search_browser(self, params):
        query = str(params.get("query", "")).strip().lower()
        if not query:
            raise ValueError("search_browser requires a non-empty query")
        category = str(params.get("category", "all")).lower()
        results = []

        def search_children(item, depth=0):
            if depth > 4 or len(results) > 50:
                return
            try:
                for child in item.children:
                    if query in child.name.lower():
                        results.append({
                            "name": child.name,
                            "uri": child.uri if hasattr(child, "uri") else "",
                            "is_loadable": child.is_loadable if hasattr(child, "is_loadable") else False,
                            "is_device": child.is_device if hasattr(child, "is_device") else False,
                        })
                    if hasattr(child, "children"):
                        search_children(child, depth + 1)
            except Exception:
                pass

        if category == "all":
            roots_to_search = list(self._available_browser_roots().values())
        else:
            roots_to_search = [self._get_browser_root(category)]

        for root in roots_to_search:
            search_children(root)

        return {"query": query, "results": results[:50], "count": len(results)}

    def _load_drum_kit(self, params):
        track = self._get_track(params["track_index"])
        rack_uri = str(params.get("rack_uri", "")).strip()
        if not rack_uri:
            raise ValueError("Must provide rack_uri")
        item = self._resolve_browser_item_by_uri(rack_uri, "load_drum_kit")
        if not getattr(item, "is_loadable", False):
            raise ValueError("load_drum_kit requires a loadable drum-kit preset URI")
        if getattr(item, "is_device", False):
            raise ValueError("load_drum_kit requires a drum-kit preset URI, not a generic device entry")
        result = self._load_browser_item_onto_track(
            track,
            item,
            mode="drum_kit_load",
            track_index=params["track_index"],
            requested_uri=rack_uri,
        )
        result["loaded"] = rack_uri
        result["stability"] = "likely-complete"
        return result
