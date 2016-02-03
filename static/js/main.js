var app = angular.module('sMusic', []);
        app.controller('mainView', function($scope, $http){
            console.log('lel');
            $scope.albumArtURL="http://drlynnjohnson.com/wp-content/uploads/2014/03/cd-dvd.jpg";
            $http.get("/api/v1/status/").success(function(response){
                $scope.volume = response['status']["vol_left"];
                $scope.trackTitle = response['status']['title'];
                $scope.trackArtist = response['status']['artist'];
                $scope.trackAlbum = response['status']['album'];
                $http.get(
                    encodeURI("http://musicbrainz.org/ws/2/release/?query=artist:" +
                            $scope.trackArtist + "+recording:" + $scope.trackAlbum + "&fmt=json")).success(
                        function(response){
                            $scope.albumMBID = response['releases'][0]["release-group"]["id"];
                            $scope.albumArtURL = "http://coverartarchive.org/release-group/"+$scope.albumMBID+"/front";
                            console.log(response);
                            console.log(encodeURI("http://musicbrainz.org/ws/2/release/?query=artist:" +
                            $scope.trackArtist + "+recording:" + $scope.trackAlbum + "&fmt=json"));
                    });
            });

            $scope.updateVolume = function(){
                $http.get("/api/v1/vol/"+$scope.volume+"/");
            }
        });