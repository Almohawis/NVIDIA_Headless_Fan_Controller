# NVIDIA Headless Fan Controller

Temperature-based GPU fan control for headless Linux systems using NVIDIA NVML and systemd.

[العربية](#arabic) | [English](#english)

![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?logo=linux&logoColor=black)
![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![NVIDIA](https://img.shields.io/badge/NVIDIA-NVML-76B900?logo=nvidia&logoColor=white)
![systemd](https://img.shields.io/badge/Service-systemd-blue)

<a id="arabic"></a>

<div dir="rtl">

## العربية

### نبذة عن المشروع

خدمة خفيفة للتحكم التلقائي في سرعة مراوح بطاقات NVIDIA على أنظمة لينكس، موجهة بشكل أساسي إلى بطاقة RTX 3090 والخوادم التي تعمل دون واجهة رسومية (Headless Servers).

تقرأ الخدمة درجة حرارة المعالج الرسومي باستخدام مكتبة NVIDIA Management Library (NVML)، وتضبط سرعة جميع المراوح القابلة للتحكم في البطاقة الأولى وفق منحنى حراري محدد. لا تتطلب X11 أو Wayland أو مكتبات Python خارجية، وتعمل في الخلفية عبر systemd.

### المميزات

- التحكم المباشر بالمراوح باستخدام NVML عبر `ctypes`.
- تحديث قراءة الحرارة كل 5 ثوانٍ.
- منحنى سرعة مراوح قابل للتعديل من الكود.
- هامش حراري (Hysteresis) بمقدار 3 درجات مئوية عند خفض السرعة لتقليل التذبذب.
- اختبار التحكم بالمراوح قبل تفعيل الخدمة.
- محاولة استعادة التحكم التلقائي الأصلي عند إيقاف البرنامج أو حدوث خطأ أثناء التشغيل.
- إعادة تشغيل الخدمة تلقائيًا عند الفشل، وتشغيلها عند إقلاع النظام بعد تثبيتها بنجاح.
- تسجيل تغييرات السرعة والأخطاء عبر systemd journal.

### منحنى المراوح الافتراضي

</div>

| GPU temperature / درجة الحرارة | Fan speed / سرعة المراوح |
| :---: | :---: |
| < 50°C | 35% |
| 50–59°C | 45% |
| 60–69°C | 65% |
| 70–74°C | 80% |
| ≥ 75°C | 90% |

<div dir="rtl">

هذه الحدود تمثل الانتقال عند ارتفاع الحرارة؛ عند انخفاضها تُطبق آلية Hysteresis. على سبيل المثال، بعد الانتقال إلى سرعة 80% عند 70°C، لا تنخفض السرعة إلى المستوى السابق إلا عند 67°C أو أقل.

### المتطلبات

- نظام Linux يستخدم systemd.
- Python 3 متاح في المسار `/usr/bin/python3`.
- تعريف NVIDIA ومكتبة `libnvidia-ml.so.1` مع دعم واجهات NVML المستخدمة والتحكم في المراوح.
- بطاقة رسومية مرئية للنظام وتحتوي على مراوح قابلة للتحكم برمجيًا.
- صلاحيات root للتثبيت وتشغيل أوامر التحكم.

المشروع موجه إلى RTX 3090، لكن توافق البطاقات الأخرى وإصدارات التعريفات يعتمد على دعم NVML ولم يُتحقق منه ضمن هذه المراجعة. في البيئات الافتراضية، يجب أن تكون البطاقة وواجهات التحكم المطلوبة متاحة داخل النظام الذي يشغّل الخدمة.

### التثبيت

نفّذ الأوامر التالية داخل مجلد المشروع بعد فك الضغط أو استنساخ المستودع:

</div>

```bash
nvidia-smi
chmod +x install.sh
sudo ./install.sh
```

<div dir="rtl">

ينسخ المثبّت الملفات إلى مسارات النظام، ثم يختبر المراوح بطلب سرعة 80% لمدة 5 ثوانٍ. يتحقق من أن نسبة السرعة المُبلّغ عنها لكل مروحة بين 60% و100%، ويحاول إعادة التحكم التلقائي. إذا فشل الاختبار يتوقف المثبّت قبل خطوة تفعيل الخدمة. عند نجاحه يفعّل الخدمة ويشغّلها ويعرض حالتها.

### إدارة الخدمة

</div>

```bash
# Service status
sudo systemctl status NvidiaFanController.service

# Live logs
sudo journalctl -u NvidiaFanController.service -f

# Start / stop / restart
sudo systemctl start NvidiaFanController.service
sudo systemctl stop NvidiaFanController.service
sudo systemctl restart NvidiaFanController.service
```

<div dir="rtl">

### اختبار المراوح واستعادة الوضع التلقائي

أوقف الخدمة أولًا لتجنب تعارض عمليتين تتحكمان في المراوح:

</div>

```bash
sudo systemctl stop NvidiaFanController.service
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --test
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --auto
```

<div dir="rtl">

لإعادة تشغيل التحكم المخصص:

</div>

```bash
sudo systemctl start NvidiaFanController.service
```

<div dir="rtl">

### تخصيص الإعدادات

عدّل الملف `NvidiaFanController.py` داخل مجلد المشروع:

</div>

```python
INTERVAL = 5
HYSTERESIS = 3
STEPS = [(-100, 35), (50, 45), (60, 65), (70, 80), (75, 90)]
```

<div dir="rtl">

القيم تمثل فترة القراءة بالثواني، وهامش خفض السرعة بالدرجات المئوية، وأزواج (عتبة الحرارة، نسبة سرعة المروحة). القيمة -100 هي الحد البرمجي للمستوى الأول.

لتطبيق التغييرات بعد التثبيت:

</div>

```bash
sudo systemctl stop NvidiaFanController.service
sudo install -m 755 NvidiaFanController.py /usr/local/sbin/NvidiaFanController.py
sudo systemctl start NvidiaFanController.service
```

<div dir="rtl">

### إلغاء التثبيت

</div>

```bash
sudo systemctl disable --now NvidiaFanController.service
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --auto
sudo rm /etc/systemd/system/NvidiaFanController.service
sudo rm /usr/local/sbin/NvidiaFanController.py
sudo systemctl daemon-reload
```

<div dir="rtl">

### القيود والتنبيهات

- يتحكم الإصدار الحالي في البطاقة ذات الفهرس NVML رقم 0 فقط، ويطبق السرعة نفسها على جميع مراوحها.
- يعتمد على حرارة نواة GPU فقط، وليس حرارة ذاكرة GDDR6X أو Hotspot.
- الحد الأقصى للمنحنى الحالي 90%؛ لا توجد آلية مستقلة للإيقاف الطارئ بسبب الحرارة.
- اختبار المراوح يتحقق من النسبة التي تُبلغ عنها NVML، وليس قياس RPM ماديًا مستقلًا.
- استعادة الوضع التلقائي محاولة برمجية وليست ضمانًا عند فقد الطاقة أو تعطل التعريف.
- راقب درجات الحرارة تحت الحمل قبل الاعتماد على المنحنى في التشغيل المستمر، وتأكد من عدم وجود برنامج آخر يتحكم بالمراوح.
- لم يُرفق ملف ترخيص مع المشروع؛ لم يُحدد ترخيص للتوزيع بعد.

</div>

---

<a id="english"></a>

## English

### Overview

NVIDIA Headless Fan Controller is a lightweight, temperature-based GPU fan control service for Linux, primarily targeting the RTX 3090 and headless server environments.

It uses the NVIDIA Management Library (NVML) directly through Python's standard `ctypes` module to read GPU temperature and adjust all controllable fans on the first GPU. It does not require X11, Wayland, or third-party Python packages, and runs as a background systemd service.

### Features

- Direct NVML fan control without a graphical session.
- Temperature polling every five seconds.
- Configurable step-based fan curve.
- Three-degree Celsius hysteresis when reducing fan speed.
- Fan-control validation before service activation.
- Best-effort restoration of the default automatic fan policy on termination or runtime failure.
- Automatic startup at boot and restart on failure after successful installation.
- Fan speed change and error logging through the systemd journal.

### Default fan curve

| GPU temperature | Fan speed |
| :---: | :---: |
| < 50°C | 35% |
| 50–59°C | 45% |
| 60–69°C | 65% |
| 70–74°C | 80% |
| ≥ 75°C | 90% |

The thresholds apply when temperature rises. A 3°C hysteresis applies when reducing speed. For example, after reaching the 80% step at 70°C, the controller drops to a lower step only at 67°C or below.

### Requirements

- Linux with systemd.
- Python 3 available at `/usr/bin/python3`.
- NVIDIA driver and `libnvidia-ml.so.1` exposing the required NVML fan-control APIs.
- A visible GPU with software-controllable fans.
- Root privileges for installation and fan-control commands.

The project targets the RTX 3090. Compatibility with other GPUs and driver versions depends on NVML support and has not been verified in this documentation review. In virtualized environments, the GPU and required control interfaces must be exposed to the operating system running the service.

### Installation

From the extracted or cloned project directory:

```bash
nvidia-smi
chmod +x install.sh
sudo ./install.sh
```

The installer copies the controller and service unit into their system locations, reloads systemd, and requests an 80% fan speed for five seconds. It checks that each fan's reported speed is between 60% and 100%, then attempts to restore automatic control. If the test fails, installation stops before the service enablement step. On success, the installer enables and starts the service and displays its status.

### Service management

```bash
sudo systemctl status NvidiaFanController.service
sudo journalctl -u NvidiaFanController.service -f

sudo systemctl start NvidiaFanController.service
sudo systemctl stop NvidiaFanController.service
sudo systemctl restart NvidiaFanController.service
```

### Manual testing and automatic control

Stop the service before running manual commands to avoid competing fan-control processes.

```bash
sudo systemctl stop NvidiaFanController.service
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --test
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --auto
```

To resume custom fan control:

```bash
sudo systemctl start NvidiaFanController.service
```

### Configuration

Edit `NvidiaFanController.py` in the project directory:

```python
INTERVAL = 5
HYSTERESIS = 3
STEPS = [(-100, 35), (50, 45), (60, 65), (70, 80), (75, 90)]
```

- `INTERVAL`: temperature polling interval in seconds.
- `HYSTERESIS`: downward transition margin in degrees Celsius.
- `STEPS`: ordered pairs of temperature thresholds and fan speed percentages. The -100 threshold is the baseline sentinel.

Apply changes after installation:

```bash
sudo systemctl stop NvidiaFanController.service
sudo install -m 755 NvidiaFanController.py /usr/local/sbin/NvidiaFanController.py
sudo systemctl start NvidiaFanController.service
```

### Project structure

```text
.
├── NvidiaFanController.py           # NVML fan-control daemon
├── NvidiaFanController.service      # systemd service unit
├── install.sh   # Installer and pre-activation test
└── README.md
```

### Uninstallation

```bash
sudo systemctl disable --now NvidiaFanController.service
sudo /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --auto
sudo rm /etc/systemd/system/NvidiaFanController.service
sudo rm /usr/local/sbin/NvidiaFanController.py
sudo systemctl daemon-reload
```

### Limitations and safety notes

- The current implementation controls NVML GPU index 0 only and applies the same target speed to all its fans.
- The controller uses GPU core temperature, not GDDR6X memory junction or hotspot temperature.
- The default curve tops out at 90%; no independent emergency thermal shutdown mechanism is implemented.
- The built-in test checks NVML-reported fan speed percentages, not independently measured physical RPM.
- Automatic fan-policy restoration is best-effort and cannot be guaranteed during power loss or driver failure.
- Monitor temperatures under sustained workloads before relying on a custom curve, and avoid running competing fan controllers.

### License

No license file was supplied with the project. Distribution and reuse terms have not yet been specified.
