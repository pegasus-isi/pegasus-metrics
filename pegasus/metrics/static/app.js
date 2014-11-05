/**
 * Created by dcbriggs on 10/22/14.
 */
define(["angular", "./router",
        "./downloads",
        "uiRouter", "angularGrid"],
function(angular, router, Downloads) {
    var appName = "pegasusMetricsApp";
    var app = angular.module(appName, ["ui.router", "ngGrid"]);

    app.factory("Downloads", Downloads);

    app.config(router.getProdConstructor());

    function getName() {
        return appName;
    }

    // Since we know this is an angular app all we need is the name and then we can call it with angular.module(app.getName);
    return {
        getName : getName
    }
});
