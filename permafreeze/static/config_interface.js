
BackupTarget = Backbone.Model.extend({
    defaults: {
        name: 'Backup target',
        dirpath: ''
    },
    initialize: function() {
    }
});

TargetList = Backbone.View.extend({
    initialize: function() {
    }
});

var target_view = new TargetList({ el: $("#target_list") });
