/**
 * Created by dcbriggs on 10/22/14.
 */

requirejs.config({
    paths : {
        angular: "//cdnjs.cloudflare.com/ajax/libs/angular.js/1.2.18/angular",
        uiRouter: "//cdnjs.cloudflare.com/ajax/libs/angular-ui-router/0.2.10/angular-ui-router",
        angularGrid: '//cdnjs.cloudflare.com/ajax/libs/ng-grid/2.0.11/ng-grid.min',
        jQuery : "//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/jquery"
    },
    shim : {
        angular : {"exports" : "angular"},
        uiRouter: {
            deps: ["angular"]
            // No export because this just adds fields into angular
        },
        angularGrid: {
            deps: ["jQuery", "angular"]
            // No export because this just adds fields into angular
        },
        jQuery : {"exports" : "$"}
    }
});

requirejs(["angular","app"], function(angular, app){
    angular.bootstrap(document, [app.getName()]);
});

