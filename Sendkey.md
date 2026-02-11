API 详细说明
发起推送
向以下 URL 发送一个 HTTP 请求，并传递参数即可。
https://sctapi.ftqq.com/****************.send
参数说明如下：
title: 消息标题，必填。最大长度为 32 。
desp: 消息内容，选填。支持 Markdown语法 ，最大长度为 32KB ,消息卡片截取前 30 显示。
short: 消息卡片内容，选填。最大长度64。如果不指定，将自动从desp中截取生成。
noip: 是否隐藏调用IP，选填。如果不指定，则显示；为1则隐藏。
channel: 动态指定本次推送使用的消息通道，选填。如不指定，则使用网站上的消息通道页面设置的通道。支持最多两个通道，多个通道值用竖线|隔开。比如，同时发送服务号和企业微信应用消息通道，则使用 9|66 。通道对应的值如下：
官方Android版·β=98
企业微信应用消息=66
企业微信群机器人=1
钉钉群机器人=2
飞书群机器人=3
Bark iOS=8
测试号=0
自定义=88
PushDeer=18
方糖服务号=9
openid: 消息抄送的openid，选填。只支持测试号和企业微信应用消息通道。测试号的 openid 从测试号页面获得 ，多个 openid 用 , 隔开。企业微信应用消息通道的 openid 参数，内容为接收人在企业微信中的 UID（可在消息通道页面配置好该通道后通过链接查看） , 多个人请 | 隔开，即可发给特定人/多个人。不填则发送给通道配置页面的接收人。
如果采用GET，请将参数通过`urlencode`编码；
如果采用 POST 方式，默认以 FORM 方式解码，
如果要通过 JSON 格式传递，请在 Header 中指定 `Content-type` 为 `application/json`，比如：
curl -X "POST" "https://sctapi.ftqq.com/key.send" -H 'Content-Type: application/json;charset=utf-8' -d ...
查询推送状态
调用发起推送接口后，我们并不是立刻调用微信接口，而是会将任务放入异步推送队列。所以返回的结果是放入队列是否成功。
如果想要查询微信发是否成功，请将其返回中的 pushid 和 readkey，发送到以下 URL 查询。
注意 pushid 是用 id 参数传递。
https://sctapi.ftqq.com/push?id={pushid}&readkey={readkey}
返回值中，wxstatus 即为微信接口返回的内容。为空则该任务可能还未执行。
调用函数
PHP
function sc_send(  $text , $desp = '' , $key = '[SENDKEY]'  )
{
    $postdata = http_build_query( array( 'text' => $text, 'desp' => $desp ));
    $opts = array('http' =>
    array(
        'method'  => 'POST',
        'header'  => 'Content-type: application/x-www-form-urlencoded',
        'content' => $postdata));
    
    $context  = stream_context_create($opts);
    return $result = file_get_contents('https://sctapi.ftqq.com/'.$key.'.send', false, $context);

}
端对端加密
新版Server酱支持消息的端对端加密。其流程为：

在调用接口之前，先将 desp 内容通过加密函数（下文会讲算法）进行加密
在调用接口时，通过 desp 传递加密后的内容，同时传递 encoded 参数 = 1
在详情页面输入加密函数中传递的密码，通过JS在客户端界面查看内容
加密函数（ PHP版 ）的参数为：

content : 需要加密的内容
key : 阅读时输入的密码
iv : 固定字串，由 SCT 和 UID 拼接而成。比如 UID 为1，那么 iv 即为 SCT1。本页面最下方可查看当前用户UID。
function sc_encode($content, $key, $iv)
{
    $key = substr(md5($key), 0, 16);
    $iv = substr(md5($iv), 0, 16);
    return openssl_encrypt(base64_encode($content), 'AES-128-CBC', $key, 0, $iv);
}
当前用户的UID为 313895