export const panel = {
    addToStatusArea(uuid, indicator) {
        this.statusArea[uuid] = indicator;
    },
    statusArea: {}
};

export default { panel };
