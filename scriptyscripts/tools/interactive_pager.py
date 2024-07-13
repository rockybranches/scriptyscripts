from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.widgets import Box, Frame
from prompt_toolkit.styles import Style


def interactive_pager(items):
    """
    Interactive pager for selecting an item from a list of items.
    """
    # Strip leading/trailing whitespace from items
    items = [item.strip() for item in items]
    selected_index = [0]

    def get_menu_text():
        result = []
        for i, item in enumerate(items):
            if i == selected_index[0]:
                result.append(('class:highlighted', f'>> {item}\n'))
            else:
                result.append(('', f'   {item}\n'))
        return result

    def up(event):
        if selected_index[0] > 0:
            selected_index[0] -= 1

    def down(event):
        if selected_index[0] < len(items) - 1:
            selected_index[0] += 1

    def select(event):
        event.app.exit(result=items[selected_index[0]])

    def quit(event):
        event.app.exit(result=None)

    kb = KeyBindings()
    kb.add('up')(up)
    kb.add('down')(down)
    kb.add('enter')(select)
    kb.add('q')(quit)

    body = Box(
        body=Frame(
            title="Select an option",
            body=Window(
                content=FormattedTextControl(
                    text=get_menu_text,
                    focusable=True,
                    key_bindings=kb,
                    modal=True
                )
            )
        )
    )

    style = Style([
        ('highlighted', 'bg:#ff0066')
    ])

    layout = Layout(HSplit([body]))
    app = Application(layout=layout, full_screen=True,
                      key_bindings=kb, style=style)

    return app.run()


if __name__ == "__main__":
    items_test = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]
    selection = interactive_pager(items_test)
    print(f"You selected: {selection}")
