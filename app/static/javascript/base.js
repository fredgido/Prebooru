const Prebooru = {};

Prebooru.postRequest = function(url, args) {
    let form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    for (let key in args) {
        let input = document.createElement('input');
        input.name = key;
        input.value = args[key];
        input.type = "hidden";
        form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
};

Prebooru.promptArgPost = function(obj, prompt_text, argname) {
    let arg = prompt(prompt_text);
    if (arg !== null) {
        console.log(arg, argname);
        Prebooru.postRequest(obj.href, {[argname]: arg});
    }
    return false;
};

Prebooru.linkPost = function(obj) {
    Prebooru.postRequest(obj.href, {});
    return false;
};

Prebooru.linkDelete = function(obj) {
    Prebooru.postRequest(obj.href, {_method: 'delete'});
    return false;
};
