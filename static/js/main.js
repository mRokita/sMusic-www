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

app.controller('librarySearch', function($scope, $http){
    $scope.query = query;
    console.log($scope.query);
    $scope.queryChange = function(){
        $scope.search();
    };
    $scope.search = function(){
        $http.get("/api/v1/search_track/"+encodeURI($scope.query)).success(function(response){
            $scope.tracks = response["tracks"];
            console.log(response);
        });
    };

    $scope.tracks = {};
    $scope.clearQueueAndPlayTrack = function(artist_id, album_id, track_id){
        console.log(artist_id+album_id+track_id);
        $http.get("/api/v1/clear_q_and_play/"+artist_id+"/"+album_id+"/"+track_id+"/");
    };

    $scope.addToQueue = function(artist_id, album_id, track_id){
        $http.get("/api/v1/add_to_q/"+artist_id+"/"+album_id+"/"+track_id+"/");
    };
    $scope.search();
});

app.controller('playerStatus', function($scope, $http, $interval){
    $scope.isFileLoaded = false;
    $scope.albumArtURL = "http://drlynnjohnson.com/wp-content/uploads/2014/03/cd-dvd.jpg";
    $scope.loadData = function(status) {
        var loadFromStatus = function (response) {
            if (typeof response === "undefined") return;
            $scope.volume = response['status']['vol_left'];
            $scope.isFileLoaded = response['status'].hasOwnProperty('file');
            $scope.isLocked = response['status']['locked'];
            $scope.isPlaying= response['status']['status'] !== "paused";
            $scope.hideButtons = $scope.isLocked && !$scope.isPlaying;
            var newAlbumArtURL;
            if($scope.isFileLoaded) {
                $scope.trackTitle = response['status'].hasOwnProperty("title") ? response['status']['title'] : response["status"]["file"];
                $scope.trackArtist = response['status'].hasOwnProperty("artist") ?  response['status']['artist'] :
                    (response["status"].hasOwnProperty('albumartist') ? response['status']['albumartist']: "Nieznany");
                $scope.trackAlbum = response['status'].hasOwnProperty('album') ? response['status']['album']: "Nieznany";
                $scope.position = response['status']['position'];
                $scope.duration = response['status']['duration'];
                $scope.duration_readable = response['status']['duration_readable'];
                newAlbumArtURL = "/api/v1/albumart/" + encodeURI($scope.trackArtist)+"/"+encodeURI($scope.trackAlbum)+"/";
                if ($scope.albumArtURL != newAlbumArtURL)
                    $scope.albumArtURL = newAlbumArtURL;
            } else {
                $scope.trackTitle = "Error: No track is loaded";
                $scope.trackArtist = "Error: No track is loaded";
                $scope.trackAlbum = "Error: No track is loaded";
                newAlbumArtURL = "http://drlynnjohnson.com/wp-content/uploads/2014/03/cd-dvd.jpg";
                if ($scope.albumArtURL != newAlbumArtURL)
                    $scope.albumArtURL = newAlbumArtURL;
                $scope.position = 0;
                $scope.duration = 0;
                $scope.duration_readable = "00:00";
            }
        };
        if (typeof status === "undefined")
            $http.get("/api/v1/status/").success(loadFromStatus);
        else
            loadFromStatus(status);
        $http.get("/api/v1/current_queue/").success(function (response){
            $scope.queue = response['queue'];
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
        $http.get("/api/v1/pause/");
    };

    $scope.playerPlay = function(){
        $http.get("/api/v1/play/");
    };

    $scope.playerNext = function(){
        $http.get("/api/v1/play_next/");
    };

    $scope.playerPrev = function(){
        $http.get("/api/v1/play_prev/");

    };

    $interval(function() {$scope.loadData();}, 1000);

});