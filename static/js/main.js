var app = angular.module('sMusic', []);
        app.controller('mainView', function($scope, $http){
            console.log('lel');
            $scope.loadData = function() {
                $scope.albumArtURL = "http://drlynnjohnson.com/wp-content/uploads/2014/03/cd-dvd.jpg";
                $http.get("/api/v1/status/").success(function (response) {
                    $scope.volume = response['status']["vol_left"];
                    $scope.trackTitle = response['status']['title'];
                    $scope.trackArtist = response['status']['artist'];
                    $scope.trackAlbum = response['status']['album'];
                    $scope.position = response['status']['position'];
                    $scope.duration = response['status']['duration'];
                    var id = setInterval(function(){
                        $scope.position++;
                        if($scope.position >= $scope.duration){
                            $scope.loadData();
                            clearInterval(id);
                        }
                    }, 1000);
                    $scope.albumArtURL = "/api/v1/albumart/" + encodeURI($scope.trackArtist)+"/"+encodeURI($scope.trackAlbum)+"/";
                    console.log($scope.albumArtURL);
                });
            };
            $scope.updateVolume = function(){
                $http.get("/api/v1/vol/"+$scope.volume+"/");
            };

            $scope.playerPause = function(){
                $http.get("/api/v1/pause/");
            };

            $scope.playerPlay = function(){
                $http.get("/api/v1/play/");
            };

            $scope.loadData();

        });