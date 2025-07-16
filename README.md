# 🛡️ Web Security: SOP, CORS и CSP на практике

## 🧾 Описание

Учебный проект для практического изучения механизмов браузерной безопасности: Same-Origin Policy (SOP), Cross-Origin Resource Sharing (CORS) и Content Security Policy (CSP).

## 🚀 Быстрый старт

```
git clone https://github.com/zhabii/sop-cors-csp.git --depth 1; \
	cd sop-cors-csp; \
	docker compose build && docker compose up -d 
```

Настройка доменов в  `hosts` (нужны права sudo/администратора)

*Linux*
```bash
echo '127.0.0.1 example.com request.example.com' >> /etc/hosts
```

*Windows*
```powershell
echo '127.0.0.1 example.com request.example.com' >> 'C:\Windows\System32\drivers\etc\hosts'
```

💢 Такие ссылки интерактивные -> [`request.example.com`](http://request.example.com) 

## 🗃 Структура проекта 

```bash
.
├── Dockerfile              
├── README.md       
├── compose.yaml               
├── flask                       
│   ├── Dockerfile 
│   ├── app.py                     
│   └── templates                  
│       ├── csp-report.html
│       ├── csp.html
│       └── index.html
├── nginx                          
│   ├── example.com.conf
│   └── request.example.com.conf
└── static                         
    ├── cors.html
    ├── index.html
    ├── script.js
    └── sop.html
```


## 🎓 Изучаем политики

### 1. Как работает SOP

**Same-Origin-Policy** - это политика безопасности браузера, которая запрещает доступ JavaScript к данным с другого источника (origin), даже если запрос был отправлен. Иначе говоря, если мы с одного источника отправляем запрос на другой, то JS не сможет прочитать ответ от этого запроса.

**Источник** - это комбинация протокола, доменного имени и порта. Если у двух страниц хоть что-то из этого отличается, то источники являются разными.

**🔒 SOP ограничивает:**
- доступ к `document`, `window`, `iframe.contentWindow`
- чтение ответов от `fetch`, `XMLHttpRequest`, если нет CORS    
- доступ к `localStorage`, `sessionStorage`, `cookies`

Посмотрим, как это работает на практике.

Переходим на [`request.example.com`](http://request.example.com) - это простая страница, которая показывает текущий origin и позволяет отправить fetch на другой.

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715133549.png)

Несмотря на то, что `request.example.com` и `example.com` похожи, браузер считает их **разными источниками**, так как их доменное имя отличается.

Нажимаем кнопку и запрос уходит. Переходим на [`example.com`](http://example.com/). Это простой логгер запросов. Среди всех запросов видим наш fetch c `request.example.com`

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715133607.png)

То есть SOP не защитил нас от отправки запроса. Иначе говоря, теоретически, мы могли бы отправить какой-нибудь сложный запрос на API с прикрепленными cookie и он бы сработал.

```js
fetch("https://bank.com/api/transfer", {
  method: "POST",
  body: JSON.stringify({ to: "attacker", amount: 100 }),
  headers: {
    "Content-Type": "application/json"
  },
  credentials: "include" 
});
```

Окей, мы выяснили, что **SOP ≠ защита от CSRF**. Он не блокирует запрос, а **не дает читать ответ**. 
Чтобы убедится в этом, переходим  на [`request.example.com/sop.html`](http://request.example.com/sop.html). Здесь мы создаем iframe, загружаем в него `example.com` и пытаемся достать его содержимое.

```js
document.getElementById('origin').textContent = window.location.origin;
        // document.domain = "example.com"
        setTimeout(() => {
            const iframe = document.getElementById("other");
            const text = iframe.contentDocument.body.innerText;
            console.log("Полученный текст:", text);
        }, 1000);
```

Открываем DevTools и получаем ошибку. Так SOP рубит любые попытки JS заглянуть в другой origin.

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715142044.png)

Можно ли обойти эти правила только на уровне SOP? Да, при соблюдении жестких условий.
1. Оба ресурса имеют общий домен второго уровня
2. Оба явно указали `document.domain = "origin.com";`
3. Протокол и порт совпадают

🤓 Для обхода этих жестких ограничений был придуман CORS - гибкая надстройка над SOP. Речь о ней пойдет в следующем блоке. То что будет показано далее - старый и небезопасный метод, который нигде не используется и рассмотрен только в учебных целях.

Окей, оба ресурса имеют общий домен `example.com`, оба работают на HTTP и проброшены на порт 80. Осталось добавить `document.domain = example.com` на оба ресурса и перезагрузить страницу. 

Заходим в DevTools и видим содержимое `example.com/` в консоли

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715142257.png)

### 2. CORS

CORS - это механизм, который расширяет SOP и позволяет браузеру читать cross-origin ответы, если сервер явно разрешил это.

Решение о блокировке принимается на основе HTTP заголовков. 
Допустим, мы отправляем запрос на bank.com

```http
GET /data HTTP/1.1
Origin: https://evil.com
```

Получаем ответ
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://evil.com
```

Браузер сравнивает того, кто сделал запрос `Origin` и того, кому можно читать ответ `Access-Control-Allow-Origin`. Если совпадение есть, данные ответа доступны для чтения JS-ом - все достаточно просто. 

Попробуем настроить CORS на лабораторном стенде. Переходим на [`request.example.com/cors.html`](http://request.example.com/cors.html). Здесь JS делает запрос на `example.com` и выводит ответ в консоль - почти то же самое, что в предыдущем кейсе, но вместо iframe используется fetchAPI

```js
fetch("http://example.com")
    .then(response => response.text())
    .then(responseText => console.log(responseText))
```

Заходим в DevTools и ловим ошибку  "*blocked by CORS policy*".

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715154409.png)

Нужно сконфигурировать веб-сервер на выдачу нужного заголовка. Заходим в `nginx/example.com.conf` и добавляем строку в блок `location /`

```nginx
add_header Access-Control-Allow-Origin "http://request.example.com";
```

Сохраняем, ребутаем и перезагружаем страницу. Содержимое `example.com` теперь в консоли.

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715154523.png)

#### 🌐 Preflight
Когда браузер сомневается в безопасности запроса, он отправляет `OPTION` серверу, чтобы узнать, можно ли отправить основной запрос. Такой механизм называется **Preflight-запросом**

Preflight работает, если 
- Метод отличен от GET, POST и HEAD
- Присутствуют нестандартные заголовки

В список стандартных заголовков входят те, которые агент пользователь автоматически добавляет к запросу + определенный список "безопасных заголовков", а именно:
- `Connection`
- `User-Agent`
- `Accept`
- `Accept-Language`
- `Content-Language`
- `Content-Type` со значениями
	- `text/plain`
	- `multipart/form-data`
	- `application/x-www-form-urlencoded`

Если запрос сложный (например POST с `Content-type: application/json` и `Authorization`), то браузер перед реальным запросом делает **Preflight**

```http
OPTIONS /data HTTP/1.1
Origin: https://evil.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization
```

```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://evil.com
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true 
```

Если в ответе есть расхождение, то основной запрос не отправится

❓ *`credentials: "include"` триггерит preflight?* - Нет, его триггерят только опасные методы и нестандартные заголовки. Но даже если cookie уходят, без `Access-Control-Allow-Credentials` JS не получить к ним доступ.

Сконфигурируем обработку preflight на веб сервере. 

```nginx
if ($request_method = OPTIONS) {
    add_header Access-Control-Allow-Origin "http://request.example.com";
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type";
    add_header Access-Control-Max-Age 600;
    add_header Content-Type text/plain;
    add_header Content-Length 0;
    return 204;
}

add_header Access-Control-Allow-Origin "http://request.example.com";
```

Попробуем отправить запрос curl-ом, чтобы убедится, что все работает.

```bash
curl -X OPTIONS -H "Host: logs.lab" http://127.0.0.1:9090 -v
```

```
* Request completely sent off
< HTTP/1.1 204 No Content
< Server: nginx/1.29.0
< Date: Fri, 11 Jul 2025 10:38:14 GMT
< Connection: keep-alive
< Access-Control-Allow-Origin: http://info.server.lab:8080
< Access-Control-Allow-Methods: GET, POST, OPTIONS
< Access-Control-Allow-Headers: Content-Type
< Content-Type: text/plain
< Content-Length: 0
```

### 3. Как работает CSP

**Content-Security-Policy** - политика браузера, которая определяет, с каких ресурсов контент может быть загружен на страницу. Она защищает от XSS, сниффинга пакетов (можно включить только контент по HTTPS) и атак внедрения данных.
Если браузер не поддерживает CSP, то он будет использовать Same-Origin-Policy 

Для управления используется заголовок `Content-Security-Policy` и `X-Content-Security-Policy` (устаревший).

```plain
Content-Security-Policy: policy
```

Альтернативно можно задать его через мета тэг
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src https://*; child-src 'none';">
```

Посмотрим наглядно, как это работает. Переходим на [`example.com/csp`](http://example.com/csp). И видим два алерта: один inline и один, загруженный с `request.example.com`

```html
<script>
	alert('CSP violation!');
</script>

<script src='http://request.example.com/script.js'></script>
```

*script.js*
```js
alert('Script from request.example.com!')
```

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715155914.png)

Предположим, нас это не устраивает такой расклад и мы хотим ограничить доступ к ресурсам с любых источников, включая текущий. А еще было бы неплохо как то перехватывать результаты блокировки, благо CSP поддерживает обе эти функции.

Для репортов используем следующий эндпойнт
```python
@app.route("/csp-report", methods=['POST', 'GET'])
def csp_report():
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True) or {}
        time_str = datetime.now().isoformat()
        log_entry = f"[{time_str}] | {json.dumps(data)}\n"

        with open("csp.log", "a") as f:
            f.write(log_entry)

        return '', 204

    try:
        with open("csp.log", "r") as f:
            return "<br>".join(f.readlines()[-30:])
    except FileNotFoundError:
        return "empty log"
```

Добавляем заголовок на сервер. 

```nginx 
add_header Content-Security-Policy "default-src 'none'; report-uri /csp-report" always;
```

Перезагружаем страницу и замечаем, что алерты не прогрузились, а на `/csp-report` появились два сообщения 

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715160632.png)

Попробуем разрешить скрипт с `request.example.com`. Для этого немного поменяем заголовок и добавим нужный origin в `script-src`

```nginx
add_header Content-Security-Policy "default-src 'none'; script-src request.example.com; report-uri /csp-report" always;
```

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715160802.png)

Перезагружаем страницу - первый алерт сработал. Попробуем разрешить второй, добавив его sha-256 в script-src (узнать ее можно в DevTools).

![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715160946.png)

```nginx
add_header Content-Security-Policy "default-src 'none'; script-src request.example.com 'sha256-F5wVOASaeLmy5Wq+L0Mii6PNmvrUW0jLgD8sm1+UFbk='; report-uri /csp-report" always;
```

Видим второй алерт и радуемся. 
![](https://github.com/zhabii/sop-cors-csp/blob/master/img/Pasted%20image%2020250715161112.png)

Аналогичным образом настраиваются любые другие ресурсы: медиа, скрипты, стили и прочее. 

## 🧠 Что важно запомнить

- **SOP** ограничивает JS-доступ к cross-origin ответам.
- **CORS** - механизм, дополняющий SOP и позволяющий серверу разрешать доступ к своим ресурсам с определенных origin-ов
- **CSP** позволяет ограничить загрузку и выполнение ресурсов (в том числе inline) на странице.

**Источник** = схема + доменное имя + порт
SOP ≠ защита от CSRF

## 📚 Полезные ссылки

Все необходимое описано в соответствующих разделах MND 
- [Same-Origin Policy](https://developer.mozilla.org/ru/docs/Web/Security/Same-origin_policy)
- [Cross-Origin Resource Sharing](https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/CORS)
- [Content Security Policy](https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/CSP)
