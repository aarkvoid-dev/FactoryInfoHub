(("undefined" !== typeof self ? self : this).webpackJsonp_N_E = ("undefined" !== typeof self ? self : this).webpackJsonp_N_E || []).push([
    [67], {
        IfFf: function(e, t, n) {
            "use strict";
            n.r(t);
            var r = n("wx14"),
                a = n("q1tI"),
                i = n.n(a),
                o = n("qSDI"),
                m = (i.a.createElement, function(e) {
                    var t = e.className,
                        n = e.title || "",
                        r = e.subTitle || "";
                    return i.a.createElement(o.a, null, i.a.createElement("div", {
                        className: "reward-content ".concat(t || "")
                    }, i.a.createElement("div", {
                        className: "reward-meta"
                    }, n && i.a.createElement("h3", null, n), r && i.a.createElement("p", null, r), i.a.createElement("div", {
                        className: "action-download"
                    }, i.a.createElement("a", {
                        href: "https://go.lbb.in/iosupdate",
                        target: "_blank",
                        rel: "noopener noreferrer"
                    }, i.a.createElement("img", {
                        src: "/static/images/appStore@1x.png",
                        srcSet: "/static/images/appStore@2x.png",
                        alt: "IOS Download Image"
                    })), i.a.createElement("a", {
                        href: "https://go.lbb.in/androidupdate",
                        target: "_blank",
                        rel: "noopener noreferrer"
                    }, i.a.createElement("img", {
                        src: "/static/images/playStore@1x.png",
                        srcSet: "/static/images/playStore@2x.png",
                        alt: "Android Download Image"
                    }))), i.a.createElement("div", {
                        className: "action-more"
                    }, i.a.createElement("a", {
                        className: "btn-more",
                        href: "https://lbb.in/perks",
                        target: "_blank",
                        rel: "noopener noreferrer"
                    }, i.a.createElement("span", null, "Learn More"))))))
                }),
                l = n("J6Do"),
                s = n.n(l),
                d = n("auMK"),
                c = (i.a.createElement, function(e) {
                    return i.a.createElement("svg", Object(r.a)({
                        fill: "#7B7B7C",
                        height: "24",
                        viewBox: "0 0 24 24",
                        width: "24",
                        xmlns: "http://www.w3.org/2000/svg"
                    }, e), i.a.createElement("path", {
                        d: "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
                    }), i.a.createElement("path", {
                        d: "M0 0h24v24H0z",
                        fill: "none"
                    }))
                });
            t.default = function(e) {
                var t = Object(d.a)().userinfo,
                    n = e.open,
                    r = e.onRequestClose,
                    a = (null === t || void 0 === t ? void 0 : t.rewardPoints) || 0,
                    o = (null === t || void 0 === t ? void 0 : t.reward_points) || a,
                    l = "We're so psyched that we're giving you ".concat(o, " Perks for signing up! Download the app to use them.");
                return i.a.createElement(s.a, {
                    modal: !1,
                    open: n,
                    onRequestClose: r,
                    className: "lbbtipModal d-md-none",
                    bodyClassName: "lbbtipModal-body",
                    bodyStyle: {
                        padding: "1.5rem 1.5rem 2rem",
                        position: "relative"
                    },
                    contentClassName: "lbbtipModal-content",
                    contentStyle: {
                        width: "calc(100% - 30px)"
                    }
                }, i.a.createElement("div", {
                    className: "lbbtip-body"
                }, i.a.createElement("div", {
                    className: "text-right"
                }, i.a.createElement("a", {
                    className: "lbbtip-close",
                    style: {
                        position: "relative",
                        right: "-10px",
                        top: "-10px"
                    }
                }, i.a.createElement(c, {
                    onClick: function() {
                        r()
                    }
                }))), i.a.createElement(m, {
                    title: "We're happy to have you here! \ud83c\udf8a",
                    subTitle: l
                })))
            }
        },
        qSDI: function(e, t, n) {
            "use strict";
            n.d(t, "a", (function() {
                return i
            })), n.d(t, "b", (function() {
                return o
            }));
            var r = n("vOnD"),
                a = n("lFMt"),
                i = r.c.div.withConfig({
                    displayName: "styled-components__StyledRewardContent",
                    componentId: "sc-1gx9lxd-0"
                })([".reward-content{text-align:center;@media (min-width:800px){text-align:left;}h3{font-size:1.6rem;font-weight:", ";margin-bottom:.8rem;@media (min-width:800px){margin-bottom:1.2rem;font-size:1.8rem;}}p{font-size:1.2rem;margin-bottom:1.2rem;@media (min-width:800px){font-size:1.4rem;}}.action-download{margin-top:1.6rem;a{display:inline-block;margin-right:1rem;&:last-child{margin-right:0;}img{object-fit:contain;width:auto;height:3.6rem;}}}.action-more{margin-top:1.6rem;.btn-more{color:", ";font-size:1.4rem;font-weight:", ";text-transform:uppercase;}}}"], a.tb, a.hb, a.tb),
                o = r.c.div.withConfig({
                    displayName: "styled-components__StyledRewardSignup",
                    componentId: "sc-1gx9lxd-1"
                })([".reward-signup{border-radius:1.2rem;overflow:hidden;.reward-header{background-color:#ffecc4;display:flex;padding:1.5rem 2.4rem;@media (min-width:800px){padding:2.4rem;}.header-image{flex:0 0 5rem;margin-right:1.2rem;img,svg{width:auto;height:6rem;}}.header-meta{flex:1;h3{font-size:1.4rem;line-height:2.2rem;font-weight:", ";margin-bottom:0;@media (min-width:800px){font-size:1.8rem;line-height:2.4rem;}}p{font-size:1.2rem;line-height:1.8rem;margin:.4rem 0 0;@media (min-width:800px){font-size:1.4rem;}}span{color:", ";}}}.reward-meta{background-color:rgba(255,175,2,0.12);padding:2rem;.signup-options{font-size:1.6rem;font-weight:", ";@media (min-width:800px){display:flex;justify-content:space-around;}margin-bottom:0;.signup-google{font-size:1.4rem;font-weight:", ";display:flex;justify-content:center;padding:1.2rem 4.9rem 1.1rem;box-shadow:1.5rem 0 3rem 0 rgba(211,212,226,0.25);border-radius:3rem;cursor:pointer;background-color:", ";.signup-google-text{margin-left:1.8rem;cursor:pointer;}}.signup-email{font-size:1.2rem;cursor:pointer;text-align:center;font-weight:", ";margin-top:1.6rem;color:", ";}}}.action-signup{margin-top:1.6rem;.btn-signup{background-color:", ";color:", ";display:block;width:100%;height:", ";line-height:", ";border-radius:2.4rem;span{color:", ";}&:disabled,&.disabled{cursor:default;pointer-events:none;background:", ";color:", ";opacity:1;span{color:", ";}}}}h3{font-size:1.2rem;}p{font-size:1.2rem;margin-bottom:1.6rem !important;}}.shipping-form{.form-control{background-color:", " !important;}}.action-download{margin-top:1.6rem;a{display:inline-block;margin-right:1rem;&:last-child{margin-right:0;}img,svg{object-fit:contain;width:auto;height:2.5rem;@media (min-width:800px){height:4.2rem;}}}}.terms-note{font-size:1rem;margin-top:2rem;text-align:center;a{color:", ";text-decoration:underline;}}}"], a.tb, a.T, a.tb, a.xb, a.yb, a.xb, a.hb, a.hb, a.yb, a.h, a.h, a.yb, a.f, a.g, a.g, a.yb, a.hb)
        }
    }
]);