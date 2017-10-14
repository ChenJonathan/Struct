//////Index one block height//////
function setHeiHeight() {
  "use strict";
  $('#promo_head').css({
    height: $(window).height() + 'px'
  });
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