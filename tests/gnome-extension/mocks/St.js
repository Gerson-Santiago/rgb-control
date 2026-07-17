import GObject from 'gi://GObject';

export const Icon = GObject.registerClass(
class Icon extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
    }
});

export const BoxLayout = GObject.registerClass(
class BoxLayout extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
        this.children = [];
    }
    add_child(child) {
        this.children.push(child);
    }
    destroy_all_children() {
        this.children = [];
    }
});

export const Button = GObject.registerClass(
class Button extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
        this.signals = {};
        this.accessible_name = '';
    }
    set_accessible_name(name) {
        this.accessible_name = name;
    }
    connect(signal, callback) {
        this.signals[signal] = callback;
        return 1;
    }
});

export default { Icon, BoxLayout, Button };
