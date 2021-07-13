const Posts = {};

Posts.createUpload = function(obj) {
    let url = prompt("Enter the URL of the post to upload from:");
    if (url !== null) {
        Prebooru.postRequest(obj.href, {'upload[request_url]': url});
    }
    return false;
}