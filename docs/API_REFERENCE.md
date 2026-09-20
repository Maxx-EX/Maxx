# Maxx API Reference — 标准库 API 全览

> 按 8 层架构组织。每个模块列出核心函数签名。
> 引导阶段：签名 + 简化实现；Level 2+ 完善。

---

## 目录

1. [core/ — 基础核心层](#1-core--基础核心层)
2. [sys/ — 系统接口层](#2-sys--系统接口层)
3. [encode/ — 编码与序列化](#3-encode--编码与序列化)
4. [net/ — 网络栈](#4-net--网络栈)
5. [crypto/ — 加密哈希](#5-crypto--加密哈希)
6. [data/ — 数据处理](#6-data--数据处理)
7. [util/ — 工具层](#7-util--工具层)
8. [platform/ — 平台适配](#8-platform--平台适配)

---

## 1. core/ — 基础核心层

> 70 个模块。类型系统、容器、迭代器、并发原语、IO 基础。

### 1.1 类型系统

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/int` | `i8/i16/i32/i64/u8/u16/u32/u64/int/uint` | 整数类型与运算 |
| `core/float` | `f32/f64` | 浮点类型 |
| `core/bool` | `true/false/! && \|\|` | 布尔运算 |
| `core/char` | `char::is_alpha/isdigit/is_space` | 字符判断 |
| `core/byte` | `byte::to_hex/from_hex` | 字节操作 |
| `core/str` | `str::len/slice/contains/index_of` | 字符串基础 |
| `core/string_builder` | `StringBuilder::new/push/to_str` | 字符串拼接 |

### 1.2 容器

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/vec` | `Vec::new/push/pop/get/set/len/slice` | 动态数组 |
| `core/deque` | `Deque::push_front/push_back/pop_front/pop_back` | 双端队列 |
| `core/queue` | `Queue::enqueue/dequeue/peek/is_empty` | 队列 |
| `core/stack` | `Stack::push/pop/peek` | 栈 |
| `core/linked_list` | `LinkedList::push/pop/insert/remove` | 链表 |
| `core/binary_heap` | `BinaryHeap::push/pop/peek` | 二叉堆 |
| `core/map/hash_map` | `HashMap::new/get/set/remove/keys/values` | 哈希表 |
| `core/map/tree_map` | `TreeMap::new/get/set/remove/range` | 有序映射 |
| `core/set/hash_set` | `HashSet::new/insert/contains/remove` | 哈希集合 |
| `core/set/tree_set` | `TreeSet::new/insert/contains/range` | 有序集合 |

### 1.3 函数式与选项

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/option` | `some(v)/none/map/unwrap/unwrap_or` | 可选值 |
| `core/result` | `ok(v)/err(e)/map/unwrap/unwrap_or_else` | 结果类型 |
| `core/either` | `left/right/is_left/is_right/map_left/map_right` | 左右值 |
| `core/iter` | `Iter::next/collect/map/filter/fold` | 迭代器 |
| `core/iter_adapter` | `chain/zip/enumerate/skip/take/flatten` | 迭代器适配器 |
| `core/fn` | `fn(A)->B` | 函数类型 |
| `core/fn_compose` | `compose/pipe/curry/partial/flip` | 函数组合 |
| `core/memoize` | `memoize(f)` | 记忆化 |
| `core/curry` | `curry(f)` | 柯里化 |

### 1.4 内存与指针

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/memory` | `malloc/free/copy/compare` | 内存操作 |
| `core/ptr` | `Ptr::read/write/offset/null` | 指针 |
| `core/box` | `Box::new/deref` | 堆分配 |
| `core/rc` | `Rc::new/clone/strong_count` | 引用计数 |
| `core/slice` | `slice::from_ptr/len/get` | 切片 |

### 1.5 并发

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/async/future` | `Future::poll/await` | Future |
| `core/async/promise` | `Promise::resolve/reject/future` | Promise |
| `core/async/task` | `Task::spawn/join/cancel` | 任务 |
| `core/async/chan` | `Chan::send/recv/try_send/try_recv` | 通道 |
| `core/sync/mutex` | `Mutex::lock/unlock/try_lock` | 互斥锁 |
| `core/sync/condvar` | `Condvar::wait/signal/broadcast` | 条件变量 |
| `core/sync/rwlock` | `RwLock::read/write/upgrade` | 读写锁 |
| `core/sync/barrier` | `Barrier::new/wait` | 屏障 |
| `core/thread` | `Thread::spawn/join/id` | 线程 |
| `core/thread_local` | `ThreadLocal::get/set` | 线程局部存储 |

### 1.6 时间与 IO

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/time/instant` | `Instant::now/elapsed` | 时间点 |
| `core/time/duration` | `Duration::secs/millis/nanos` | 时间段 |
| `core/time/timer` | `Timer::after/interval` | 定时器 |
| `core/io/reader` | `Reader::read/read_line/read_all` | 读流 |
| `core/io/writer` | `Writer::write/write_line/flush` | 写流 |
| `core/io/buffer` | `Buffer::new/put/get` | 缓冲 |

### 1.7 其他核心

| 模块 | 核心 API | 说明 |
|---|---|---|
| `core/panic` | `panic(msg)/catch_unwind` | 异常 |
| `core/assert` | `assert/assert_eq/assert_ne` | 断言 |
| `core/comptime` | `comptime` | 编译期计算 |
| `core/type_id` | `type_of<T>/type_name` | 类型标识 |
| `core/trait` | `trait/impl` | 特征 |
| `core/error` | `Error::new/kind/chain` | 错误 |
| `core/fmt` | `format/Display` | 格式化 |
| `core/parse` | `parse<T>(s)` | 解析 |
| `core/hash` | `hash<T>(v)` | 哈希 |
| `core/eq` | `eq<T>/ne<T>` | 相等性 |
| `core/ord` | `cmp<T>/lt/le/gt/ge` | 排序 |

---

## 2. sys/ — 系统接口层

> 50 个模块。文件、进程、环境、终端、用户、系统信息、动态库、FFI。

### 2.1 文件系统

| 模块 | 核心 API |
|---|---|
| `sys/fs/file` | `open/read/write/close/seek` |
| `sys/fs/dir` | `mkdir/rmdir/list_dir/cwd` |
| `sys/fs/path` | `join/basename/dirname/ext/normalize` |
| `sys/fs/walk` | `walk(dir)/collect_files` |
| `sys/fs/watch` | `watch(path)/on_change` |
| `sys/fs/metadata` | `stat/size/mtime/is_file/is_dir` |
| `sys/fs/perm` | `chmod/chown/exists` |
| `sys/fs/symlink` | `symlink/readlink` |

### 2.2 进程

| 模块 | 核心 API |
|---|---|
| `sys/process/spawn` | `spawn(cmd, args)/pid` |
| `sys/process/args` | `args()/arg(i)` |
| `sys/process/env` | `env(key)/set_env(key, val)` |
| `sys/process/exit` | `exit(code)` |
| `sys/process/signal` | `signal(sig, handler)` |
| `sys/process/pipe` | `pipe()/read/write` |
| `sys/process/child` | `wait/kill/terminate` |

### 2.3 环境与终端

| 模块 | 核心 API |
|---|---|
| `sys/env/get` | `get(key) -> ?str` |
| `sys/env/set` | `set(key, val)` |
| `sys/env/home` | `home() -> str` |
| `sys/env/temp` | `temp() -> str` |
| `sys/terminal/tty` | `is_tty()/cols/rows` |
| `sys/terminal/color` | `red/green/blue/reset/bold` |
| `sys/terminal/cursor` | `move_to/hide/show/clear` |
| `sys/terminal/input` | `read_key/read_line` |

### 2.4 系统信息

| 模块 | 核心 API |
|---|---|
| `sys/system/os` | `os_name() -> "linux"/"android"/...` |
| `sys/system/arch` | `arch() -> "arm64"/"x86_64"/...` |
| `sys/system/cpu` | `cpu_count()/cpu_freq` |
| `sys/system/mem` | `total_mem()/free_mem()` |
| `sys/system/uptime` | `uptime() -> Duration` |
| `sys/system/hostname` | `hostname() -> str` |

### 2.5 动态库与 FFI

| 模块 | 核心 API |
|---|---|
| `sys/dynlib/load` | `load(path) -> Library` |
| `sys/dynlib/symbol` | `get_sym(lib, name) -> Ptr` |
| `sys/dynlib/unload` | `unload(lib)` |
| `sys/ffi/call` | `call(ptr, args...) -> Ret` |
| `sys/ffi/ptr` | `ptr::from_int/to_int/null` |
| `sys/ffi/callback` | `callback::new(fn) -> Ptr` |

---

## 3. encode/ — 编码与序列化

> 45 个模块。UTF、Base、JSON、YAML、TOML、XML、CSV、URL、HTML、二进制缓冲。

### 3.1 字符编码

| 模块 | 核心 API |
|---|---|
| `encode/utf8` | `encode/decode/validate/length` |
| `encode/utf16` | `encode/decode/little_endian/big_endian` |
| `encode/utf32` | `encode/decode` |
| `encode/unicode/normalize` | `NFC/NFD/NFKC/NFKD` |
| `encode/unicode/width` | `display_width(str) -> int` |
| `encode/unicode/grapheme` | `graphemes(str) -> Iter<char>` |

### 3.2 Base 系列

| 模块 | 核心 API |
|---|---|
| `encode/base64` | `encode(data) -> str/decode(str) -> Vec<u8>` |
| `encode/base32` | `encode/decode` |
| `encode/base58` | `encode/decode` |
| `encode/hex` | `encode(data) -> str/decode(str) -> Vec<u8>` |
| `encode/octal` | `encode/decode` |
| `encode/binary_str` | `to_binary_str/from_binary_str` |

### 3.3 序列化格式

| 模块 | 核心 API |
|---|---|
| `encode/json/parse` | `parse(str) -> Result<Json, str>` |
| `encode/json/stringify` | `stringify(j) -> str/pretty(j, indent)` |
| `encode/json/value` | `Json::Null/Bool/Num/Str/Arr/Obj` |
| `encode/json/path` | `get_path(j, "$.a.b[0]") -> ?Json` |
| `encode/yaml` | `parse/stringify` |
| `encode/toml` | `parse/stringify` |
| `encode/xml` | `parse/stringify` |
| `encode/csv` | `parse(str) -> Vec<Vec<str>>/to_csv(rows)` |
| `encode/msgpack` | `encode/decode` |
| `encode/protobuf` | `encode/decode` |

### 3.4 URL / HTML / MIME

| 模块 | 核心 API |
|---|---|
| `encode/url` | `encode/decode/parse/join` |
| `encode/html/escape` | `escape_html/unescape_html` |
| `encode/html/entity` | `entity::decode(name) -> char` |
| `encode/mime/type` | `mime_type(path) -> str` |
| `encode/multipart` | `encode/decode` |

### 3.5 二进制缓冲

| 模块 | 核心 API |
|---|---|
| `encode/buffer/read` | `read_u8/u16/u32/u64/f32/f64` |
| `encode/buffer/write` | `write_u8/u16/u32/u64/f32/f64` |
| `encode/buffer/byte_order` | `little_endian/big_endian/native` |
| `encode/binary/varint` | `encode_varint/decode_varint` |

---

## 4. net/ — 网络栈

> 53 个模块。TCP、UDP、IP、DNS、HTTP、WebSocket、TLS、FTP、SMTP、SSH、代理。

### 4.1 TCP / UDP

| 模块 | 核心 API |
|---|---|
| `net/tcp/listener` | `listen(port) -> Listener/accept() -> Stream` |
| `net/tcp/stream` | `connect(host, port)/read/write/close` |
| `net/udp/socket` | `bind(port)/send_to/recv_from` |

### 4.2 IP / DNS

| 模块 | 核心 API |
|---|---|
| `net/ip/addr` | `IpAddr::v4/v6/parse` |
| `net/ip/v4` | `Ipv4Addr::new/parse/loopback` |
| `net/ip/v6` | `Ipv6Addr::new/parse/loopback` |
| `net/dns/resolve` | `resolve(hostname) -> Vec<IpAddr>` |
| `net/dns/lookup` | `lookup(name, record_type) -> Vec<Record>` |

### 4.3 HTTP

| 模块 | 核心 API |
|---|---|
| `net/http/client` | `Client::new/get/post/put/delete` |
| `net/http/request` | `Request::new/method/url/headers/body` |
| `net/http/response` | `Response::status/body/headers/json` |
| `net/http/header` | `Header::get/set/contains` |
| `net/http/cookie` | `Cookie::new/get/set` |
| `net/http/server` | `Server::listen/get/post/use` |
| `net/http/router` | `Router::add/get/post/group` |
| `net/http/middleware` | `Middleware::cors/logger/auth` |
| `net/http/websocket/client` | `ws_connect(url)/send/recv/close` |
| `net/http/websocket/server` | `ws_listen/on_connect/on_message/broadcast` |

### 4.4 TLS / 其他

| 模块 | 核心 API |
|---|---|
| `net/tls/connect` | `tls_connect(host, port) -> TlsStream` |
| `net/tls/accept` | `tls_accept(stream) -> TlsStream` |
| `net/socket/select` | `select(read_fds, write_fds, timeout)` |
| `net/proxy/http` | `http_proxy(url, proxy)` |
| `net/proxy/socks` | `socks5_connect(host, port, proxy)` |
| `net/ftp/client` | `ftp_connect/login/download/upload` |
| `net/smtp/client` | `smtp_connect/send_mail` |
| `net/ssh/client` | `ssh_connect/exec/close` |

---

## 5. crypto/ — 加密哈希

> 46 个模块。哈希、对称加密、非对称加密、KDF、MAC、证书、签名、随机数。

### 5.1 哈希

| 模块 | 核心 API |
|---|---|
| `crypto/hash/md5` | `md5(data) -> str` |
| `crypto/hash/sha1` | `sha1(data) -> str` |
| `crypto/hash/sha256` | `sha256(data) -> str` |
| `crypto/hash/sha512` | `sha512(data) -> str` |
| `crypto/hash/sha3` | `sha3_256(data) -> str` |
| `crypto/hash/blake2` | `blake2b(data) -> str` |
| `crypto/hash/blake3` | `blake3(data) -> str` |
| `crypto/hash/crc32` | `crc32(data) -> u32` |
| `crypto/hash/xxhash` | `xxhash64(data, seed) -> u64` |

### 5.2 对称加密

| 模块 | 核心 API |
|---|---|
| `crypto/sym/aes/gcm` | `aes_256_gcm_encrypt/decrypt` |
| `crypto/sym/aes/cbc` | `aes_256_cbc_encrypt/decrypt` |
| `crypto/sym/chacha20` | `chacha20_encrypt/decrypt` |
| `crypto/sym/salsa20` | `salsa20_encrypt/decrypt` |

### 5.3 非对称加密

| 模块 | 核心 API |
|---|---|
| `crypto/asym/rsa/gen` | `rsa_generate(bits) -> KeyPair` |
| `crypto/asym/rsa/sign` | `rsa_sign(privkey, msg) -> Signature` |
| `crypto/asym/rsa/verify` | `rsa_verify(pubkey, msg, sig) -> bool` |
| `crypto/asym/ed25519` | `ed25519_keypair/sign/verify` |
| `crypto/asym/x25519` | `x25519_shared(secret, pub) -> Shared` |

### 5.4 KDF / MAC / 其他

| 模块 | 核心 API |
|---|---|
| `crypto/kdf/pbkdf2` | `pbkdf2(password, salt, iterations, dklen) -> Key` |
| `crypto/kdf/scrypt` | `scrypt(password, salt, n, r, p) -> Key` |
| `crypto/kdf/argon2` | `argon2id(password, salt) -> Key` |
| `crypto/mac/hmac` | `hmac_sha256(key, msg) -> str` |
| `crypto/mac/poly1305` | `poly1305(key, msg) -> Tag` |
| `crypto/rand/secure` | `secure_random(n) -> Vec<u8>` |
| `crypto/rand/uuid` | `uuid_v4() -> str` |
| `crypto/otp/totp` | `totp_generate(secret) -> str/verify(secret, code)` |
| `crypto/cert/x509` | `x509_parse(cert) -> CertInfo` |

---

## 6. data/ — 数据处理

> 60 个模块。排序、搜索、树、图、压缩、数据库、统计、容器扩展。

### 6.1 排序与搜索

| 模块 | 核心 API |
|---|---|
| `data/sort/quick` | `quick_sort(arr)` |
| `data/sort/merge` | `merge_sort(arr)` |
| `data/sort/heap` | `heap_sort(arr)` |
| `data/sort/insertion` | `insertion_sort(arr)` |
| `data/sort/tim` | `tim_sort(arr)` |
| `data/search/binary` | `binary_search(arr, target) -> ?int` |
| `data/search/linear` | `linear_search(arr, target) -> ?int` |

### 6.2 树与图

| 模块 | 核心 API |
|---|---|
| `data/tree/bst` | `BST::insert/search/delete/inorder` |
| `data/tree/avl` | `AVL::insert/search/delete` |
| `data/tree/redblack` | `RBTree::insert/search/delete` |
| `data/tree/trie` | `Trie::insert/search/starts_with` |
| `data/graph/bfs` | `bfs(graph, start) -> Vec<Node>` |
| `data/graph/dfs` | `dfs(graph, start) -> Vec<Node>` |
| `data/graph/dijkstra` | `dijkstra(graph, start, end) -> ?Path` |
| `data/graph/astar` | `astar(graph, start, end, heuristic) -> ?Path` |

### 6.3 压缩

| 模块 | 核心 API |
|---|---|
| `data/compress/gzip` | `gzip_compress(data) -> Vec<u8>/decompress(data)` |
| `data/compress/deflate` | `deflate_compress/inflate` |
| `data/compress/zip` | `zip_create(path)/zip_extract(path)` |

### 6.4 数据库

| 模块 | 核心 API |
|---|---|
| `data/db/sqlite` | `sqlite_connect(path)/query/prepare` |
| `data/db/mysql` | `mysql_connect(host, user, pass, db)` |
| `data/db/postgres` | `postgres_connect(url)` |
| `data/db/redis` | `redis_connect/get/set/pubsub` |

### 6.5 统计

| 模块 | 核心 API |
|---|---|
| `data/statistics/mean` | `mean(arr) -> f64` |
| `data/statistics/median` | `median(arr) -> f64` |
| `data/statistics/stddev` | `stddev(arr) -> f64` |
| `data/statistics/correlation` | `correlation(x, y) -> f64` |
| `data/statistics/regression` | `linear_regression(x, y) -> (slope, intercept)` |

### 6.6 容器扩展

| 模块 | 核心 API |
|---|---|
| `data/lru` | `LRUCache::new/get/set/evict` |
| `data/lfu` | `LFUCache::new/get/set` |
| `data/ring` | `RingBuffer::new/push/pop` |
| `data/bloom` | `BloomFilter::add/contains` |
| `data/collection_ext/chunk` | `chunk(arr, n) -> Vec<Vec<T>>` |
| `data/collection_ext/window` | `window(arr, n) -> Vec<Vec<T>>` |
| `data/collection_ext/group_by` | `group_by(arr, key_fn) -> Map<K, Vec<T>>` |

---

## 7. util/ — 工具层

> 50 个模块。日期、时区、i18n、正则、日志、测试、CLI、验证、随机、单位、日历。

### 7.1 日期与时间

| 模块 | 核心 API |
|---|---|
| `util/date/parse` | `parse(str) -> DateTime` |
| `util/date/format` | `format(dt, pattern) -> str` |
| `util/date/calc` | `add_days/add_months/diff` |
| `util/timezone/list` | `list_timezones() -> Vec<str>` |
| `util/timezone/convert` | `convert_tz(dt, from, to) -> DateTime` |

### 7.2 i18n

| 模块 | 核心 API |
|---|---|
| `util/i18n/translate` | `t(key, locale) -> str` |
| `util/i18n/format_number` | `format_number(n, locale) -> str` |
| `util/i18n/plural` | `plural(n, locale) -> str` |

### 7.3 日志与测试

| 模块 | 核心 API |
|---|---|
| `util/log/logger` | `debug/info/warn/error(msg)` |
| `util/log/level` | `set_level(level)` |
| `util/test/runner` | `run_tests() -> TestStats` |
| `util/test/case` | `describe/it/assert` |
| `util/test/bench` | `bench(name, fn) -> Duration` |

### 7.4 CLI

| 模块 | 核心 API |
|---|---|
| `util/cli/arg` | `parse_args(argv) -> CliArgs` |
| `util/cli/flag` | `flag(args, name, default) -> bool` |
| `util/cli/help` | `help() -> str` |
| `util/cli/color` | `red/green/blue/bold/reset` |
| `util/cli/progress` | `progress_bar(total)/update(n)` |

### 7.5 验证

| 模块 | 核心 API |
|---|---|
| `util/validation/email` | `is_email(s) -> bool` |
| `util/validation/phone` | `is_phone(s) -> bool/is_chinese_phone` |
| `util/validation/url` | `is_url(s) -> bool` |
| `util/validation/ip` | `is_ipv4/is_ipv6(s) -> bool` |
| `util/validation/uuid` | `is_uuid(s) -> bool` |

### 7.6 单位与日历

| 模块 | 核心 API |
|---|---|
| `util/unit/length` | `m_to_km/m_to_ft/m_to_mile` |
| `util/unit/weight` | `kg_to_lb/lb_to_kg` |
| `util/unit/temperature` | `c_to_f/f_to_c/c_to_k` |
| `util/unit/data_size` | `bytes_to_kb/kb_to_mb/format_size` |
| `util/calendar/lunar` | `solar_to_lunar/lunar_to_solar` |
| `util/calendar/holiday` | `is_holiday(date) -> bool` |

---

## 8. platform/ — 平台适配

> 41 个模块。Linux、Windows、macOS、Android、iOS、WASM、浏览器、桌面、移动端。

### 8.1 桌面平台

| 模块 | 核心 API |
|---|---|
| `platform/linux/file` | Linux 文件系统特定调用 |
| `platform/linux/socket` | Linux socket 特定选项 |
| `platform/linux/process` | Linux 进程控制 |
| `platform/windows/file` | Windows 文件 API |
| `platform/windows/registry` | Windows 注册表 |
| `platform/macos/file` | macOS 文件 API |
| `platform/macos/fsevents` | macOS 文件事件 |

### 8.2 移动平台

| 模块 | 核心 API |
|---|---|
| `platform/android/asset` | `open_asset(path) -> Stream` |
| `platform/android/jni` | `jni_call(env, class, method)` |
| `platform/android/intent` | `start_intent(action, data)` |
| `platform/android/activity` | `get_activity() -> Activity` |
| `platform/ios/ui` | `ios_uikit_view()` |
| `platform/ios/nsstring` | `nsstring::from_str/to_str` |

### 8.3 Web / 浏览器

| 模块 | 核心 API |
|---|---|
| `platform/wasm/bindings` | `wasm_export/wasm_import` |
| `platform/wasm/webgl` | `webgl::create_context/draw` |
| `platform/browser/dom` | `dom::query/set_text/add_event` |
| `platform/browser/fetch` | `fetch(url) -> Promise<Response>` |

### 8.4 桌面 UI

| 模块 | 核心 API |
|---|---|
| `platform/desktop/window` | `window::new/show/close` |
| `platform/desktop/dialog` | `dialog::open_file/save_file/alert` |

### 8.5 FFI 与插件

| 模块 | 核心 API |
|---|---|
| `platform/ffi/c_call` | `c_call(func, args...) -> Ret` |
| `platform/ffi/struct` | `ffi_struct::new/pack/unpack` |
| `platform/ffi/callback` | `callback::new(fn) -> Ptr` |
| `platform/plugin/load` | `load_plugin(path) -> Plugin` |
| `platform/plugin/register` | `register(name, fn) -> ()` |

---

## 统计

| 层 | 模块数 | 核心领域 |
|---|---|---|
| core/ | 70 | 类型、容器、迭代器、并发、IO |
| sys/ | 50 | 文件、进程、环境、终端、FFI |
| encode/ | 45 | 编码、序列化、JSON、URL、HTML |
| net/ | 53 | TCP/HTTP/WebSocket/TLS/DNS |
| crypto/ | 46 | 哈希、加密、签名、证书 |
| data/ | 60 | 排序、搜索、图、数据库、统计 |
| util/ | 50 | 日期、i18n、测试、CLI、验证 |
| platform/ | 41 | Linux/Windows/macOS/Android/iOS/Web |
| **总计** | **415** | **全栈标准库** |
