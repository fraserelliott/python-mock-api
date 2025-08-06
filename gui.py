from dearpygui.dearpygui import *
from server import server
import time
from threading import Timer

log_messages = []
_last_refresh_time = 0


def strip_status_prefix(item: str) -> str:
    return item.split(" ", 1)[1]


def get_route_items():
    items = []
    for route in sorted(server.routes):
        if server.fail_next.get(route, False):
            items.append(f"[FAILING] {route}")
        else:
            items.append(f"[PASSING] {route}")
    return items


def get_middleware_items():
    items = []
    for mw in server.middleware.keys():
        key = f"middleware:{mw}"
        if server.fail_next.get(key, False):
            items.append(f"[FAILING] {mw}")
        else:
            items.append(f"[PASSING] {mw}")
    return items


def log_info(message):
    log_messages.append(message)
    # Limit max logs to last 100 to keep UI snappy
    if len(log_messages) > 100:
        log_messages.pop(0)
    set_value("logger_text", "\n".join(log_messages))


def reset_data_callback():
    server.reset_datasets()
    log_info("Datasets reset.")


def fail_route_confirm_callback(sender, app_data, user_data):
    # get current value of route dropdown
    selected = get_value("route_combo")
    if selected:
        selected = strip_status_prefix(selected)
        server.fail_next[selected] = True
        configure_item("route_combo", items=get_route_items())
        log_info(f"Set to fail next call to: {selected}")
        set_value("route_combo", "")


def fail_middleware_confirm_callback(sender, app_data, user_data):
    selected = get_value("middleware_combo")
    if selected:
        selected = f"middleware:{strip_status_prefix(selected)}"
        server.fail_next[selected] = True
        configure_item("middleware_combo", items=get_middleware_items())
        log_info(f"Set to fail next call to: {selected}")
        set_value("middleware_combo", "")


def build_gui():
    with window(label="Mock Server Control", width=785, height=565, pos=(0, 0), no_title_bar=True, no_resize=True, no_move=True, no_collapse=True):
        with child_window(height=180, width=-1, border=False):
            add_text("Fail next call to:")
            with group(horizontal=True):
                add_combo(
                    tag="route_combo",
                    items=get_route_items(),
                    width=500
                )
                add_button(label="Confirm Route",
                           callback=fail_route_confirm_callback)
            add_spacer(height=10)
            add_text("Fail next call requiring:")
            with group(horizontal=True):
                add_combo(
                    tag="middleware_combo",
                    items=get_middleware_items(),
                    width=500
                )
                add_button(label="Confirm Middleware",
                           callback=fail_middleware_confirm_callback)
            add_spacer(height=10)
            add_button(label="Reset Data", callback=reset_data_callback)
        add_text("Logs:")
        add_input_text(
            tag="logger_text",
            multiline=True,
            readonly=True,
            height=-1,
            width=-1
        )


def launch_gui():
    create_context()
    create_viewport(title="SCHISM", width=800, height=600, resizable=False)
    build_gui()
    setup_dearpygui()
    show_viewport()

    refresh_interval = 1.0  # seconds
    last_refresh_time = 0

    while is_dearpygui_running():
        now = time.time()
        if now - last_refresh_time >= refresh_interval:
            last_refresh_time = now
            configure_item("route_combo", items=get_route_items())
            configure_item("middleware_combo", items=get_middleware_items())
        render_dearpygui_frame()
        time.sleep(0.01)  # tiny sleep to avoid hogging CPU

    # start_dearpygui()
    destroy_context()
