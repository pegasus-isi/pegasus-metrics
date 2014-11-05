/**
 * Created by dcbriggs on 10/27/14.
 */

define([],
function() {
    return function($http) {
        var downloads = null;
        function getAll() {
            if(!downloads) {
                // Start polling from back-end
            }
            return downloads;
        }

        function pullDownloads() {
            $http.get('/downloads').success(function(data) {
                console.log(data);
            }).error(function(data) {
                // TODO: figure out what to do when you get an error
            });
        }

        return {
            getAll : getAll
        }
    }
});