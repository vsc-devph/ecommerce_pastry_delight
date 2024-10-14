$("button").click(function () {
    let target = $(this).attr('id');
    target_id = target
    if (target.indexOf("addtocart_") >= 0){
        target_id = target.replace("addtocart_", "")

        frm_action = $("#frm_addtocart").attr("action")
        url_action = frm_action.split("/")
        last_id = url_action[url_action.length-1]
        new_action = frm_action.replace(last_id,target_id)
        $("#frm_addtocart").attr("action",new_action)

        get_item_link = new_action.replace("add_cart","get_item")
        $.ajax({
            url: get_item_link,
            data: { item_id: target_id },
            type: "GET",
            success: function (data) {
                $("h5#cart_item_name").text(data.name)
                $("div#cart_item_desc").text(data.description)
                $("#cart_item_qty").val(data.qty)

                img = window.location+"static/images/products/cupcake.png"

                if (data.img_path)
                {
                    img = window.location+"/static/images/products/"+ data.img_path
                }

                $("img#card_item_img").attr("src", img);
            }
        });


    }

    if (target == 'btn_discount'){
        hostname = location.hostname+":"+location.port
        code =  $("#discount_code").val()
        discount_link = "/apply_discount"


        $.ajax({
            url: discount_link ,
            data: { discount_code: code },
            type: "GET",
            success: function (data) {
                $("#order_subtotal").text(data.subtotal.toFixed(2))
                $("#order_discount").text(data.discount.toFixed(2))
                $("#order_total").text(data.total.toFixed(2))
            }
        });
    }

});