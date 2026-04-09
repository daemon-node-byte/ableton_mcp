"""Live UI and view-selection operations."""

from __future__ import absolute_import, print_function, unicode_literals


class ViewOpsMixin(object):
    """UI view helpers."""

    def _get_current_view(self):
        app_view = self.application().view
        for view_name in ("Session", "Arranger", "Detail/Clip", "Detail/DeviceChain", "Browser"):
            try:
                if app_view.is_view_visible(view_name):
                    return {"view": view_name}
            except Exception:
                pass
        return {"view": "unknown"}

    def _focus_view(self, params):
        view_name = str(params["view"])
        try:
            self.application().view.show_view(view_name)
            return {"view": view_name}
        except Exception as exc:
            return {"view": view_name, "error": str(exc)}

    def _show_detail_view(self, params):
        detail_type = str(params.get("detail", "Detail/Clip"))
        try:
            self.application().view.show_view(detail_type)
            return {"view": detail_type}
        except Exception as exc:
            return {"view": detail_type, "error": str(exc)}
