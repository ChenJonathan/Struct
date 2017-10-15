//Get Calls
var apiRoute = '/api/' + sessionStorage.repoAuthor + '/' 
    + sessionStorage.repoName + '/' + sessionStorage.repoBranch;

function getAllNodes() {
    $.ajax({
        type: 'GET',
        url: apiRoute,
        dataType: 'json',
        success: function(data) {
            console.log(data);
        }
    });
}

function deleteNode(nodeID) {
    $.ajax({
        type: 'DELETE',
        contentType: "application/json",        
        url: apiRoute + '/file',
        dataType: 'json',
        data: {
            "file_id": nodeID
        },
        success: function(data) {
            console.log(data);
        }
    })
}

function addEdge(edgeSource, edgeTarget) {
    $.ajax({
        type: 'POST',
        contentType: "application/json",        
        url: apiRoute + '/edge',
        dataType: 'json',
        data: {
            source: edgeSource,
            target: edgeTarget
        },
        success: function(data) {
            console.log(data);
        }
    })
}

function deleteEdge(edgeSource, edgeTarget) {
    $.ajax({
        type: 'DELETE',
        url: apiRoute + '/edge',
        dataType: 'json',
        data: {
            source: edgeSource,
            target: edgeTarget
        },
        success: function(data) {
            console.log(data);
        }
    })
}

function setNodeTag(nodeID, tag) {
    $.ajax({
        type: 'PUT',
        url: apiRoute + '/file/' + nodeID + '/tag/' + tag,
        dataType: 'json',
        success: function(data) {
            console.log(data);
        }
    })
}

function setTagColor(tag, colorHex) {
    $.ajax({
        type: 'PUT',
        contentType: "application/json",                
        url: apiRoute + '/tag/' + tag + '/color/' + colorHex,
        dataType: 'json',
        success: function(data) {
            console.log(data);
        }
    })

}


$(function() {
    console.log('starting now');
    getAllNodes();
    deleteNode(4);
    addEdge(3,6);
    deleteEdge(3,6);
    setNodeTag(4, 'testtag');
    setTagColor('testtag', '%234e0550');
});

