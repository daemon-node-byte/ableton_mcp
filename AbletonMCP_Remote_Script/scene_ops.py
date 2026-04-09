"""Scene operations."""

from __future__ import absolute_import, print_function, unicode_literals


class SceneOpsMixin(object):
    """Scene CRUD and selection commands."""

    def _get_all_scenes(self):
        scenes = []
        for index, scene in enumerate(self.song().scenes):
            scenes.append({
                "index": index,
                "name": scene.name,
                "color": getattr(scene, "color", 0),
            })
        return {"scenes": scenes}

    def _create_scene(self, params):
        index = int(params.get("index", -1))
        self.song().create_scene(index)
        created_index = len(self.song().scenes) - 1 if index == -1 else index
        return {"index": created_index, "name": self.song().scenes[created_index].name}

    def _delete_scene(self, params):
        index = int(params["scene_index"])
        self.song().delete_scene(index)
        return {"deleted_index": index}

    def _fire_scene(self, params):
        scene = self.song().scenes[int(params["scene_index"])]
        scene.fire()
        return {"ok": True}

    def _stop_scene(self, params):
        scene_index = int(params["scene_index"])
        for track in self.song().tracks:
            track.clip_slots[scene_index].stop()
        return {"ok": True}

    def _set_scene_name(self, params):
        scene = self.song().scenes[int(params["scene_index"])]
        scene.name = str(params["name"])
        return {"name": scene.name}

    def _set_scene_color(self, params):
        scene = self.song().scenes[int(params["scene_index"])]
        scene.color = int(params["color"])
        return {"color": scene.color}

    def _duplicate_scene(self, params):
        index = int(params["scene_index"])
        self.song().duplicate_scene(index)
        return {"original_index": index}

    def _select_scene(self, params):
        scene = self.song().scenes[int(params["scene_index"])]
        self.song().view.selected_scene = scene
        return {"selected_scene_index": int(params["scene_index"])}

    def _get_selected_scene(self):
        selected = self.song().view.selected_scene
        for index, scene in enumerate(self.song().scenes):
            if scene == selected:
                return {"index": index, "name": scene.name}
        return {"index": -1, "name": selected.name if selected else ""}
