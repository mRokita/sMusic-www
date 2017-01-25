function is_touch_device() {  
    try {  
        document.createEvent("TouchEvent");
        return true; 
    } catch (e) {  
        return false;  
    }       
}



function str_pad_left(string) {
    return ("0"+string).slice(-2);
}

function idFromTag(tag){
    tag = tag.toLowerCase();
    var ret = "";
    for(var a in tag){
        if("abcdefghijklmnopqrstuvwxyz1234567890".indexOf(tag[a]) != -1){
            ret += tag[a];
        }
    }
    return ret;
}

function findTrackWithId(track_id, tracks){
    var track;
    for(var id in tracks){
        if(tracks.hasOwnProperty(id)){
            if(tracks[id]["id"] === track_id){
                track = tracks[id];
                break;
            }
        }
    }
    return track
}

var app = angular.module('sMusic', ['ngCookies', 'as.sortable']);
app.run(function($rootScope, $http, $cookies){
    $rootScope.isTouch = is_touch_device();
    $rootScope.change_radio = function(id){
        $http.get("/api/v1/change_radio/"+id).success(function(response){
            location.reload();
        });
    };
    $rootScope.change_radio_anonymous = function(id){
        var expireDate = new Date();
        expireDate.setDate(expireDate.getDate() + 365);
        $cookies.put('radio', id, {'expires': expireDate});
        location.reload();
    }
});

app.controller('libraryPlaylists', function($scope, $http){
    $scope.playlist_name = null;
    $scope.loadData = function(){
        $http.get('/api/v1/playlists/').success(function(response){
            $scope.playlists = response["playlists"];
        });
    };
    $scope.createPlaylist = function(){
        if(!$scope.playlist_name) return;
        for(var i in $scope.playlists){
            if($scope.playlists[i]['id'] === idFromTag($scope.playlist_name)){
                Materialize.toast('BŁĄD: Playlista o nazwie "'+$scope.playlists[i]['name']+'" już istnieje!', 3000);
                return;
            }
        }
        $http.get('/api/v1/create_playlist/' + $scope.playlist_name + '/').success(function(response){
            $scope.playlists = response["playlists"];
        });
    };
    $scope.loadData();
});

app.controller('libraryPlaylistView', function($scope, $http, $window){
    $scope.items = ['apple', 'pineapple', 'pen'];
    $scope.dragControlListeners = {
        itemMoved: function (event) {
            console.log('moved');
        },

        orderChanged: function(event) {
            $http.get('/api/v1/change_playlist_order/' + playlist_id + '/'
                + event.source.index + '/' + event.dest.index + '/').success(function(response){
               $scope.playlist = response["playlist"];
            });
        },
        clone: false,
        allowDuplicates: false
    };
    $scope.loadData = function(){
        $http.get('/api/v1/playlists/' + playlist_id).success(function(response){
            $scope.playlist = response["playlist"];
        });
    };
    $scope.delPlaylist = function(){
        $http.get("/api/v1/del_playlist/" + $scope.playlist.id).success(function(){
            $window.location.href='/playlists/';
        })
    };
    $scope.clearQueueAndPlayTrack = function(artist_id, album_id, track_id){
        $http.get("/api/v1/clear_q_and_play/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.playlist.tracks);
            Materialize.toast('Odtwarzanie ' + track["title"], 3000);
        });
    };

    $scope.addToQueue = function(artist_id, album_id, track_id){
        $http.get("/api/v1/add_to_q/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.playlist.tracks);
            Materialize.toast('Dodano ' + track["title"] + ' do kolejki', 3000);
        })
    };

    $scope.addPlaylistToQueue = function(playlist_id){
        $http.get("/api/v1/add_playlist_to_queue/" + playlist_id + "/").success(function(response){
           Materialize.toast('Dodano playlistę do kolejki!');
        });
    };

    $scope.clearQueueAndPlayPlaylist = function(playlist_id){
        $http.get("/api/v1/clear_q_and_play_playlist/" + playlist_id + "/").success(function(response){
           Materialize.toast('Rozpoczęto odtwarzanie playlisty!');
        });
    };

    $scope.delTrackFromPlaylist = function(playlist_id, track_num){
        $http.get("/api/v1/del_track_from_playlist/" + playlist_id + "/" + track_num + "/").success(function(response){
            $scope.playlist = response["playlist"];
            Materialize.toast("Element usunięto");
        });
    };

    $scope.getPlaylists = function(){
        $http.get('/api/v1/playlists/').success(function(response){
            $scope.playlists = response["playlists"];
        });
    };
    $scope.loadData();
});

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
    $scope.lastOpenedModal = null;
    $scope.loadData = function(){
        $scope.artist = artist;
        $scope.album = album;
        $scope.albumArtURL = "/static/images/nocover.jpg";
        $http.get("/api/v1/library/"+$scope.artist+"/"+$scope.album+"/").success(function(response){
            $scope.tracks = response["tracks"];
            $scope.artist_name = response["artist_name"];
            $scope.album_name = response["album_name"];
            $scope.albumArtURL = "/api/v1/albumart/" + encodeURI($scope.artist_name)+"/"+encodeURI($scope.album_name)+"/"
        });
    };

    $scope.clearQueueAndPlayTrack = function(track_id){
        $http.get("/api/v1/clear_q_and_play/"+$scope.artist+"/"+$scope.album+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Odtwarzanie ' + track["title"], 3000);
        })
    };

    $scope.addToQueue = function(track_id){
        $http.get("/api/v1/add_to_q/"+$scope.artist+"/"+$scope.album+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Dodano '+track["title"]+' do kolejki', 3000);
        });
    };
    $scope.addToPlaylist = function(playlist_id, artist_id, album_id, track_id){
        $http.get("/api/v1/add_track_to_playlist/"+playlist_id+"/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Dodano ' + track["title"] + ' do playlisty ' + playlist_id, 3000);
            $scope.lastOpenedModal.modal('close');
        });
    };

    $scope.openModal = function(index){
        $scope.lastOpenedModal = $("#playlist-modal-"+index);
        $scope.lastOpenedModal.modal();
        $scope.lastOpenedModal.modal('open');
        $scope.getPlaylists();
    };

    $scope.getPlaylists = function(){
        $http.get('/api/v1/playlists/').success(function(response){
            $scope.playlists = response["playlists"];
        });
    };
    $scope.loadData();
});

app.controller('librarySearch', function($scope, $http){
    $scope.query = query;
    $scope.lastOpenedModal = null;
    $scope.playlists = [];
    console.log($scope.query);
    $scope.queryChange = function(){
        $scope.search();
    };
    $scope.search = function(){
        $http.get("/api/v1/search_track/"+encodeURI($scope.query)).success(function(response){
            $scope.tracks = response["tracks"];
            $scope.query_current = $scope.query;
        });
    };

    $scope.tracks = {};
    $scope.clearQueueAndPlayTrack = function(artist_id, album_id, track_id){
        $http.get("/api/v1/clear_q_and_play/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Odtwarzanie ' + track["title"], 3000);
        });
    };

    $scope.addToQueue = function(artist_id, album_id, track_id){
        $http.get("/api/v1/add_to_q/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Dodano ' + track["title"] + ' do kolejki', 3000);
        })
    };

    $scope.getPlaylists = function(){
        $http.get('/api/v1/playlists/').success(function(response){
            $scope.playlists = response["playlists"];
        });
    };

    $scope.addToPlaylist = function(playlist_id, artist_id, album_id, track_id){
        $http.get("/api/v1/add_track_to_playlist/"+playlist_id+"/"+artist_id+"/"+album_id+"/"+track_id+"/").success(function(response){
            track = findTrackWithId(track_id, $scope.tracks);
            Materialize.toast('Dodano ' + track["title"] + ' do playlisty ' + playlist_id, 3000);
            $scope.lastOpenedModal.modal('close')
        });
    };

    $scope.openModal = function(index){
        $scope.lastOpenedModal = $("#playlist-modal-"+index);
        $scope.lastOpenedModal.modal();
        $scope.lastOpenedModal.modal('open');
        $scope.getPlaylists();
    };
    $scope.search();
});

app.controller('playerStatus', function($scope, $http, $interval){
    $scope.isFileLoaded = false;
    $scope.blockQueue = false;
    $scope.cachedQueue = null;
    $scope.queueMd5 = null;
    $scope.downloadedQueueMd5 = null;
    $scope.reloadQueue = false;
    $scope.queuePosition = null;
    $scope.albumArtURL = "/static/images/nocover.jpg";
    $scope.loadData = function(status) {
        var loadFromStatus = function (response) {
            if (typeof response === "undefined") return;
            $scope.volume = response['status']['vol_left'];
            $scope.reloadQueue = $scope.downloadedQueueMd5 !== response['status']['queue_md5'];
            $scope.queueMd5 = response['status']['queue_md5'];
            $scope.isFileLoaded = response['status'].hasOwnProperty('file');
            $scope.queuePosition = parseInt(response['status']['queue_position']);
            $scope.isLocked = response['status']['locked'];
            $scope.isPlaying = response['status']['status'] == "playing";
            $scope.mode = response['status']['mode'];
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
                newAlbumArtURL = "/static/images/nocover.jpg";
                if ($scope.albumArtURL != newAlbumArtURL)
                    $scope.albumArtURL = newAlbumArtURL;
                $scope.position = 0;
                $scope.duration = 0;
            }
            $scope.position_readable = str_pad_left((($scope.position-$scope.position%60))/60).toString()+":"+str_pad_left(($scope.position%60).toString());
            $scope.duration_readable = str_pad_left((($scope.duration-$scope.duration%60))/60).toString()+":"+str_pad_left(($scope.duration%60).toString());
        };
        if (typeof status === "undefined")
            $http.get("/api/v1/status/").success(loadFromStatus);
        else
            loadFromStatus(status);
        if($scope.reloadQueue){
            $http.get("/api/v1/current_queue/").success(function (response){
                if(!$scope.blockQueue)
                    $scope.queue = response['queue'];
                $scope.downloadedQueueMd5 = $scope.queueMd5;
                $scope.cachedQueue = jQuery.extend(true, {}, response['queue']);
            });
        }
    };

    $scope.toggleMode = function(){
        $http.get("/api/v1/toggle_mode/").success(function(response){
            $scope.mode = response["mode"];
        })
    };

    $scope.isModeNormal = function(){
        return $scope.mode === "normal";
    };

    $scope.getModeIcon = function(){
        switch ($scope.mode){
            case "normal":
                return "repeat";
            case "repeat":
                return "repeat";
            case "repeat_one":
                return "repeat_one"
        }
    };
    $scope.setQueuePosition = function(pos){
        $http.get('/api/v1/set_queue_position/' + pos +'/').success(function(response){
            $scope.queue = response["queue"];
        });
    };

    $scope.delFromQueue = function(pos){
        $http.get('/api/v1/del_from_queue/' + pos +'/').success(function(response){
            $scope.queue = response["queue"];
        });
    };

    $scope.dragControlListeners = {

        dragStart: function(event){
            $scope.blockQueue = true;
            $scope.oldQueue = jQuery.extend(true, {}, $scope.cachedQueue);
        },

        dragEnd: function(event){
            $scope.blockQueue = false;
        },

        orderChanged: function(event) {
            var track = $scope.oldQueue[event.source.index];
            var track2 = $scope.cachedQueue[event.source.index];
            var dest = $scope.oldQueue[event.dest.index];
            var dest2 = $scope.cachedQueue[event.dest.index];
            if(track.album === track2.album
                && track.artist === track2.artist
                && track.id === track2.id
                && dest.id === dest2.id
                && dest.album === dest2.album
                && dest.artist === dest2.artist) {
                $http.get('/api/v1/move_queue_item/' + event.source.index + '/' + event.dest.index + '/')
                    .success(function(response){
                    $scope.queue = response['queue'];
                });
            } else {
                jQuery.extend(true, $scope.queue, $scope.cachedQueue);
            }
        },

        clone: false,
        allowDuplicates: false
    };

    $scope.idFromTag = idFromTag;
    $scope.clearQueue = function () {
        $http.get("/api/v1/clear_queue/").success(function(){
            $scope.queue = [];
        });
    };

    $scope.updateVolume = function(){
        $http.get("/api/v1/vol/"+$scope.volume+"/");
    };

    $scope.seek = function(){
        $http.get('/api/v1/seek/'+$scope.position+'/');
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
    $scope.loadData();

});

app.controller('downloadStatus', function($scope, $http, $interval){
    $scope.loadStatus = function() {
        $http.get("/api/v1/download_status/").success(function (response){
            if(response['status'] == "downloading") {
                $scope.progress = response['progress'] * 100;
                $scope.speed = response['speed'];
                $scope.eta = response['eta'] + "s.";
                $scope.is_downloading = 1;
                $scope.progress_known = (response['progress'] < 0.98 && response['eta'] > 10);
            } else {
                $scope.is_downloading = 0;
            }
        });
    };

    $scope.titleFromYtUrl = function(url){
        splittedUrl = url.split("/");
        return splittedUrl[splittedUrl.length-1]
    };

    $scope.loadQueue = function() {
        $http.get("/api/v1/current_download_queue/").success(function (response){
            $scope.queue = response['queue'];
        });
    };

    $scope.clearDownloadQueue = function(){
        $http.get("/api/v1/clear_download_queue/").success(function(){
            $scope.queue = [];
        });
    };

    $interval(function() {$scope.loadStatus();}, 500);
    $interval(function() {$scope.loadQueue();}, 3000);
    $scope.loadStatus();
    $scope.loadQueue();
});
