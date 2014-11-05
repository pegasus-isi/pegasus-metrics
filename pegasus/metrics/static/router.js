/**
 * Created by dcbriggs on 10/22/14.
 */

define(['./ctrl/homepageCtrl'],
function(homepageCtrl) {
    function routes($stateProvider, $urlRouterProvider) {
        $urlRouterProvider.otherwise('/');

        $stateProvider.state('home', {
            url : '/',
            template : '../templates/home.html',
            controller : 'homepageCtrl'
        });
    }

    function getProdConstructor() {
        return ["$stateProvider", "$urlRouterProvider", routes];
    }

    function getTestConstructor() {
        return routes;
    }

    return {
        getProdConstructor : getProdConstructor,
        getTestConstructor : getTestConstructor
    };
});