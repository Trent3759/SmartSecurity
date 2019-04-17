function load(page){
    $.get( "/" + page, function( data ) {
        $( ".result" ).html( data );
          }).fail(function(){
            $.get( "/error_page", function( data ) {
                $( ".result" ).html( data );
                  })
          });
    $('a').removeClass('is-active');
    $(this).addClass('is-active')
};