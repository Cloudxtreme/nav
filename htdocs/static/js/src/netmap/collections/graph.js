define([
    'netmap/models/graph',
    'libs/backbone'
], function (netmapModel) {
    var graphCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/graph',
        initialize: function () {
            // set url depending on netmap
        }

    });

    return graphCollection;
});