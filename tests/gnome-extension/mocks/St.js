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

export const Button = GObject.registerClass({
    GTypeName: 'RgbStButton'
}, class Button extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
        this.signals = {};
        this.accessible_name = '';
    }
    set_child(child) {
        this.child = child;
    }
    set_accessible_name(name) {
        this.accessible_name = name;
    }
    connect(signal, callback) {
        this.signals[signal] = callback;
        return 1;
    }
});

export const Label = GObject.registerClass({
    GTypeName: 'RgbStLabel'
}, class Label extends GObject.Object {
    _init(params) {
        super._init();
        Object.assign(this, params);
    }
    set_text(t) {
        this.text = t;
    }
});

export default { Icon, BoxLayout, Button, Label };
