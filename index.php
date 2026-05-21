<?php
$uri = $_SERVER["REQUEST_URI"];
$uri = str_replace("/inventory-website", "", $uri);
$url = "http://127.0.0.1:5001" . $uri;
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
$response = "";
curl_setopt($ch, CURLOPT_WRITEFUNCTION, function($ch, $data) use (&$response) {
    $response .= $data;
    return strlen($data);
});
curl_setopt($ch, CURLOPT_HEADERFUNCTION, function($ch, $header) {
    $len = strlen($header);
    $header = trim($header);
    if (preg_match('/^content-type:/i', $header)) {
        header($header);
    }
    return $len;
});
$method = $_SERVER["REQUEST_METHOD"];
if ($method === "POST") {
    curl_setopt($ch, CURLOPT_POST, true);
    $body = file_get_contents("php://input");
    if ($body) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        $contentType = $_SERVER["CONTENT_TYPE"] ?? "";
        if ($contentType) {
            curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: " . $contentType]);
        }
    }
} elseif ($method !== "GET") {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
}
curl_exec($ch);
curl_close($ch);

if (strpos($response, '<!DOCTYPE') === 0 || strpos($response, '<html') !== false) {
    $response = str_replace('href="/', 'href="/inventory-website/', $response);
    $response = str_replace('src="/static/', 'src="/inventory-website/static/', $response);
    $response = str_replace('fetch("/api', 'fetch("/inventory-website/api', $response);
    $response = str_replace("fetch('/api", "fetch('/inventory-website/api", $response);
} else {
    // JSON API - fix image URLs in JSON
    $response = str_replace('"/static/', '"/inventory-website/static/', $response);
    $response = str_replace("'/static/", "'/inventory-website/static/", $response);
}
echo $response;