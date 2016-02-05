var app = angular.module('sMusic', []);
app.controller('libraryMainView', function($scope, $http){
    $scope.loadData = function(){
        $http.get("/api/v1/library/").success(function(response){
            $scope.artists = response["artists"];
        });
    };
    $scope.loadData();
});

app.controller('libraryArtistAlbums', function($scope, $http){
    $scope.loadData = function(){
        $scope.artist = artist;
        $http.get("/api/v1/library/"+$scope.artist+"/").success(function(response){
            $scope.albums = response["albums"];
            $scope.artist_name = response["artist_name"];
        });
    };
    $scope.loadData();
});

app.controller('libraryArtistAlbumTracks', function($scope, $http){
    $scope.loadData = function(){
        $scope.artist = artist;
        $scope.album = album;
        $http.get("/api/v1/library/"+$scope.artist+"/"+$scope.album+"/").success(function(response){
            $scope.tracks = response["tracks"];
            $scope.artist_name = response["artist_name"];
            $scope.album_name = response["album_name"];
        });
    };

    $scope.clearQueueAndPlayTrack = function(track_id){
        $http.get("/api/v1/clear_q_and_play/"+$scope.artist+"/"+$scope.album+"/"+track_id+"/");
    };

    $scope.addToQueue = function(track_id){
        $http.get("/api/v1/add_to_q/"+$scope.artist+"/"+$scope.album+"/"+track_id+"/");
    };

    $scope.loadData();
});

app.controller('playerStatus', function($scope, $http, $interval){
    $scope.loadData = function(status) {
        if (typeof $scope.id !== "undefined"){
            $interval.cancel($scope.id);
        }
        $scope.albumArtURL = "http://drlynnjohnson.com/wp-content/uploads/2014/03/cd-dvd.jpg";
        var loadFromStatus = function (response) {
            $scope.volume = response['status']['vol_left'];
            $scope.isPlaying = response['status'].hasOwnProperty('file');
            if($scope.isPlaying) {
                $scope.trackTitle = response['status'].hasOwnProperty("title") ? response['status']['title'] : response["status"]["file"];
                $scope.trackArtist = response['status'].hasOwnProperty("artist") ?  response['status']['artist'] :
                    (response["status"].hasOwnProperty('albumartist') ? response['status']['albumartist']: "Nieznany");
                $scope.trackAlbum = response['status'].hasOwnProperty('album') ? response['status']['album']: "Nieznany";
                $scope.position = response['status']['position'];
                $scope.duration = response['status']['duration'];
                $scope.duration_readable = response['status']['duration_readable'];
                $scope.albumArtURL = "/api/v1/albumart/" + encodeURI($scope.trackArtist)+"/"+encodeURI($scope.trackAlbum)+"/";
            } else {
                $scope.trackTitle = "Error: No track is loaded";
                $scope.trackArtist = "Error: No track is loaded";
                $scope.trackAlbum = "Error: No track is loaded";
                $scope.position = 0;
                $scope.duration = 0;
                $scope.duration_readable = "00:00";
            }
            if(response['status']['status'] === 'playing')
                $scope.id = $interval(function(){
                    $scope.position++;
                    if($scope.position >= $scope.duration){
                        $scope.loadData();
                        $interval.cancel($scope.id);
                    }
                }, 1000);
        };
        if (typeof status === "undefined")
            $http.get("/api/v1/status/").success(loadFromStatus);
        else
            loadFromStatus(status);
        $http.get("/api/v1/current_queue/").success(function (response){
            $scope.queue = response['queue'];
            console.log($scope.queue);
        });
    };

    $scope.clearQueue = function () {
        $http.get("/api/v1/clear_queue/").success(function(){
            $scope.queue = [];
        });
    };
    $scope.updateVolume = function(){
        $http.get("/api/v1/vol/"+$scope.volume+"/");
    };

    $scope.playerPause = function(){
        $http.get("/api/v1/pause/").success(function(res){
            $scope.loadData(res);
        });
    };

    $scope.playerPlay = function(){
        $http.get("/api/v1/play/").success(function(res){
            $scope.loadData(res);
        });
    };

    $scope.playerNext = function(){
        $http.get("/api/v1/play_next/").success(function(res) {
            $scope.loadData(res);
        })
    };

    $scope.playerPrev = function(){
        $http.get("/api/v1/play_prev/").success(function(res){
            $scope.loadData(res);
        });

    };

    $scope.loadData();

});