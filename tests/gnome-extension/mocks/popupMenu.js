import GObject from 'gi://GObject';

export const PopupMenuItem = GObject.registerClass(
class PopupMenuItem extends GObject.Object {
    _init(text, params) {
        super._init();
        this.text = text;
        this.params = params;
        this.label = {
            text: text,
            set_text(t) {
                this.text = t;
            }
        };
    }
});

export const PopupSeparatorMenuItem = GObject.registerClass(
class PopupSeparatorMenuItem extends GObject.Object {
    _init() {
        super._init();
    }
});

export const PopupBaseMenuItem = GObject.registerClass(
class PopupBaseMenuItem extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
        this.children = [];
    }
    add_child(child) {
        this.children.push(child);
    }
});

export const PopupImageMenuItem = GObject.registerClass(
class PopupImageMenuItem extends GObject.Object {
    _init(text, iconName, params) {
        super._init();
        this.text = text;
        this.iconName = iconName;
        this.params = params;
        this.signals = {};
    }
    connect(signal, callback) {
        this.signals[signal] = callback;
        return 1;
    }
});

export default { PopupMenuItem, PopupSeparatorMenuItem, PopupBaseMenuItem, PopupImageMenuItem };
