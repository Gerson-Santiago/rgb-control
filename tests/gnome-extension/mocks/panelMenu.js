import GObject from 'gi://GObject';

export const Button = GObject.registerClass(
class Button extends GObject.Object {
    _init(menuAlignment, name, reactive) {
        super._init();
        this.menuAlignment = menuAlignment;
        this.name = name;
        this.reactive = reactive;
        this.children = [];
        this.menu = {
            items: [],
            addMenuItem(item) {
                this.items.push(item);
            }
        };
    }
    add_child(child) {
        this.children.push(child);
    }
});

export default { Button };
