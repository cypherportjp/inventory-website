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
    if (stripos($header, 'content-type:') === 0) {
        header($header);
    }
    return $len;
});

$method = $_SERVER["REQUEST_METHOD"];
if ($method === "POST") {
    $body = file_get_contents("php://input");
    if ($body !== false && $body !== '') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        $contentType = $_SERVER["CONTENT_TYPE"] ?? '';
        $headers = [];
        if ($contentType) {
            $headers[] = "Content-Type: $contentType";
        } else {
            $headers[] = "Content-Type: application/json";
        }
        $contentLength = $_SERVER["CONTENT_LENGTH"] ?? '';
        if ($contentLength) {
            $headers[] = "Content-Length: $contentLength";
        }
        if (!empty($headers)) {
            curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        }
    }
} elseif ($method !== "GET") {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
}

curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if (strpos($response, '<!DOCTYPE') === 0 || strpos($response, '<html') !== false) {
    $response = str_replace('href="/', 'href="/inventory-website/', $response);
    $response = str_replace('src="/static/', 'src="/inventory-website/static/', $response);
    $response = str_replace('fetch("/api', 'fetch("/inventory-website/api', $response);
    $response = str_replace("fetch('/api", "fetch('/inventory-website/api", $response);
} else {
    $response = str_replace('"/static/', '"/inventory-website/static/', $response);
    $response = str_replace("'/static/", "'/inventory-website/static/", $response);
}

http_response_code($httpCode);
echo $response;
