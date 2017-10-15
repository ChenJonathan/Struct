//////Index one block height//////
function setHeiHeight() {
  "use strict";
  $('#promo_head').css({
    height: $(window).height() + 'px'
  });
}

function navigateStruct() {
  //Get url
  var url = $('#urlInput').val();

  //We assume that we can trust ourselves
  url = url.substring(url.indexOf("github") + 11);
  var inputVals = url.split("/");

  window.sessionStorage.setItem("repoAuthor", inputVals[0]);
  window.sessionStorage.setItem("repoName", inputVals[1]);
  window.sessionStorage.setItem("repoBranch", inputVals[3]);

  window.location.href = "/struct";
}

$(document).ready(function () {
  "use strict";
  //////Page load//////
  $("body").css("display", "none");
  $("body").fadeIn(900);
  $("a.transition").click(function(event){
    "use strict";
    event.preventDefault();
    linkLocation = this.href;
    $("body").fadeOut(900, redirectPage);
  });
  function redirectPage() {
    "use strict";
    window.location = linkLocation;
  }
});