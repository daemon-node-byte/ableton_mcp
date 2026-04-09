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
        browser = self.application().browser
        category = str(params.get("category_type", "all")).lower()
        category_map = {
            "instruments": browser.instruments,
            "audio_effects": browser.audio_effects,
            "midi_effects": browser.midi_effects,
            "drums": browser.drums,
            "sounds": browser.sounds,
            "samples": browser.samples,
            "all": None,
        }

        if category == "all":
            result = {}
            for key, root in [
                ("instruments", browser.instruments),
                ("audio_effects", browser.audio_effects),
                ("midi_effects", browser.midi_effects),
                ("drums", browser.drums),
                ("sounds", browser.sounds),
                ("packs", browser.packs),
                ("user_library", browser.user_library),
            ]:
                try:
                    children = list(root.children)[:15]
                    result[key] = [
                        {"name": child.name, "uri": child.uri if hasattr(child, "uri") else ""}
                        for child in children
                    ]
                except Exception:
                    pass
            return result

        root = category_map.get(category)
        if root is None:
            raise ValueError("Unknown category: {}".format(category))
        return self._get_browser_item_info(root, max_depth=2)

    def _get_browser_items_at_path(self, params):
        path = str(params.get("path", ""))
        browser = self.application().browser
        parts = [part.strip() for part in path.split("/") if part.strip()]
        top_map = {
            "instruments": browser.instruments,
            "audio_effects": browser.audio_effects,
            "midi_effects": browser.midi_effects,
            "drums": browser.drums,
            "sounds": browser.sounds,
            "samples": browser.samples,
            "packs": browser.packs,
            "user_library": browser.user_library,
        }

        if not parts:
            items = []
            for name, root in top_map.items():
                try:
                    items.append({"name": name, "uri": root.uri if hasattr(root, "uri") else ""})
                except Exception:
                    pass
            return {"items": items, "path": ""}

        current = top_map.get(parts[0].lower())
        if current is None:
            raise ValueError("Unknown browser root: {}".format(parts[0]))

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
        query = str(params.get("query", "")).lower()
        category = str(params.get("category", "all")).lower()
        browser = self.application().browser
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
                        })
                    if hasattr(child, "children"):
                        search_children(child, depth + 1)
            except Exception:
                pass

        roots_to_search = []
        if category == "all" or category == "instruments":
            roots_to_search.append(browser.instruments)
        if category == "all" or category == "audio_effects":
            roots_to_search.append(browser.audio_effects)
        if category == "all" or category == "drums":
            roots_to_search.append(browser.drums)
        if category == "all" or category == "sounds":
            roots_to_search.append(browser.sounds)

        for root in roots_to_search:
            search_children(root)

        return {"query": query, "results": results[:50], "count": len(results)}

    def _load_drum_kit(self, params):
        track = self._get_track(params["track_index"])
        rack_uri = str(params.get("rack_uri", "")).strip()
        if not rack_uri:
            raise ValueError("Must provide rack_uri")
        browser = self.application().browser
        self.song().view.selected_track = track
        item = browser.get_item_by_uri(rack_uri) if hasattr(browser, "get_item_by_uri") else None
        if item is None:
            raise ValueError("Browser item not found for URI: {}".format(rack_uri))
        browser.load_item(item)
        return {"ok": True, "loaded": rack_uri, "stability": "unverified"}
