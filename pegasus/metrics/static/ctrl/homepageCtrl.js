/**
 * Created by dcbriggs on 10/27/14.
 */

define([],
function(){
    function homepageCtrl($scope, Downloads) {
        
    }

    function getProdConstructor() {
        return ['$scope', homepageCtrl];
    }

    function getTestConstructor() {
        return homepageCtrl;
    }

    return {
        getProdConstructor : getProdConstructor,
        getTestConstructor : getTestConstructor
    }
});