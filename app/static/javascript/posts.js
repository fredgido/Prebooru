const Posts = {};

Posts.createUpload = function(obj) {
    let url = prompt("Enter the URL of the post to upload from:");
    if (url !== null) {
        Prebooru.postRequest(obj.href, {'upload[request_url]': url});
    }
    return false;
}

Posts.deleteSimilarPost = function(obj) {
    if (confirm('Remove item from similar posts?')) {
        Prebooru.linkDelete(obj);
    }
    return false;
}
