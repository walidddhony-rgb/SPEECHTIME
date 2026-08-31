import customtkinter as ctk
import tkinter.messagebox as messagebox

# إعداد المظهر العام للواجهة
ctk.set_appearance_mode("System")  # يدعم الوضع الليلي والنهاري حسب النظام
ctk.set_default_color_theme("blue")

class SpeechScribeGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # إعدادات النافذة الرئيسية
        self.title("SpeechScribe - نظام التفريغ الصوتي شبه الآلي")
        self.geometry("800x500")
        self.resizable(False, False)

        # بيانات وهمية لمحاكاة المجموعات الصوتية (Clusters)
        self.clusters_data = [
            {"id": 1, "occurrences": 12500, "time": "0.00s", "char": ""},
            {"id": 2, "occurrences": 9800,  "time": "0.25s", "char": ""},
            {"id": 3, "occurrences": 7200,  "time": "0.50s", "char": ""},
            {"id": 4, "occurrences": 6500,  "time": "0.75s", "char": ""},
            {"id": 5, "occurrences": 4300,  "time": "1.10s", "char": ""}
        ]
        self.current_index = 0
        self.total_clusters = len(self.clusters_data)

        self.setup_ui()
        self.load_cluster_data()

    def setup_ui(self):
        # --- تقسيم الشاشة ---
        # الشريط الجانبي (Sidebar)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")

        # منطقة العمل الرئيسية (Main Workspace)
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # --- عناصر الشريط الجانبي ---
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SpeechScribe 🎙️", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10))

        self.info_label = ctk.CTkLabel(self.sidebar_frame, text="الملف: lecture.wav\nالمدة: 2 ساعة", text_color="gray")
        self.info_label.pack(padx=20, pady=10)

        self.progress_label = ctk.CTkLabel(self.sidebar_frame, text="نسبة الإنجاز:", font=ctk.CTkFont(size=14))
        self.progress_label.pack(padx=20, pady=(30, 5))

        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame)
        self.progress_bar.pack(padx=20, pady=10)
        self.progress_bar.set(0)

        # زر الإنهاء
        self.finish_btn = ctk.CTkButton(self.sidebar_frame, text="إنهاء وبدء التفريغ ⚡", fg_color="#28a745", hover_color="#218838", command=self.finish_transcription)
        self.finish_btn.pack(padx=20, pady=(150, 20), side="bottom")

        # --- عناصر منطقة العمل الرئيسية ---
        self.cluster_title = ctk.CTkLabel(self.main_frame, text="المجموعة الصوتية #1", font=ctk.CTkFont(size=24, weight="bold"))
        self.cluster_title.pack(pady=(30, 10))

        self.stats_label = ctk.CTkLabel(self.main_frame, text="عدد التكرارات: 0 | الظهور الأول: 0.00s", font=ctk.CTkFont(size=14), text_color="gray")
        self.stats_label.pack(pady=(0, 30))

        # زر تشغيل الصوت (محاكاة)
        self.play_btn = ctk.CTkButton(self.main_frame, text="▶ تشغيل العينة الصوتية (25ms)", width=250, height=40, font=ctk.CTkFont(size=15), command=self.play_audio)
        self.play_btn.pack(pady=10)

        # حقل إدخال الحرف
        self.char_entry = ctk.CTkEntry(self.main_frame, placeholder_text="أدخل الحرف هنا (مثال: ا, ب, م)", width=250, height=50, font=ctk.CTkFont(size=20), justify="center")
        self.char_entry.pack(pady=20)
        self.char_entry.bind("<Return>", lambda event: self.next_cluster()) # الانتقال للتالي عند الضغط على Enter

        # أزرار التنقل
        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.nav_frame.pack(pady=30)

        self.prev_btn = ctk.CTkButton(self.nav_frame, text="السابق", width=100, command=self.prev_cluster)
        self.prev_btn.grid(row=0, column=0, padx=20)

        self.next_btn = ctk.CTkButton(self.nav_frame, text="التالي (Enter)", width=100, command=self.next_cluster)
        self.next_btn.grid(row=0, column=1, padx=20)

    def load_cluster_data(self):
        """تحديث الواجهة ببيانات المجموعة الحالية"""
        data = self.clusters_data[self.current_index]
        self.cluster_title.configure(text=f"المجموعة الصوتية #{data['id']} من {self.total_clusters}")
        self.stats_label.configure(text=f"عدد التكرارات: {data['occurrences']} | الظهور الأول: {data['time']}")
        
        # تفريغ أو تعبئة حقل الإدخال
        self.char_entry.delete(0, 'end')
        if data['char']:
            self.char_entry.insert(0, data['char'])
            
        # تحديث شريط التقدم
        progress = (self.current_index) / self.total_clusters
        self.progress_bar.set(progress)
        
        # تفعيل/تعطيل أزرار التنقل
        self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
        
        self.char_entry.focus() # التركيز على حقل الإدخال تلقائياً

    def save_current_input(self):
        """حفظ الحرف المدخل في الذاكرة"""
        current_char = self.char_entry.get().strip()
        self.clusters_data[self.current_index]['char'] = current_char

    def next_cluster(self):
        self.save_current_input()
        if self.current_index < self.total_clusters - 1:
            self.current_index += 1
            self.load_cluster_data()
        else:
            self.progress_bar.set(1.0)
            messagebox.showinfo("اكتمل العمل", "لقد قمت بتصنيف جميع المجموعات! يمكنك الآن الضغط على زر الإنهاء.")

    def prev_cluster(self):
        self.save_current_input()
        if self.current_index > 0:
            self.current_index -= 1
            self.load_cluster_data()

    def play_audio(self):
        """محاكاة تشغيل الصوت"""
        self.play_btn.configure(text="🔊 جاري التشغيل...", fg_color="#ffcc00", text_color="black")
        self.after(500, lambda: self.play_btn.configure(text="▶ تشغيل العينة الصوتية (25ms)", fg_color=["#3a7ebf", "#1f538d"], text_color=["gray10", "#DCE4EE"]))

    def finish_transcription(self):
        self.save_current_input()
        unlabeled = sum(1 for c in self.clusters_data if not c['char'])
        
        if unlabeled > 0:
            confirm = messagebox.askyesno("تحذير", f"يوجد {unlabeled} مجموعات لم يتم تصنيفها بعد. هل أنت متأكد من رغبتك في المتابعة؟")
            if not confirm:
                return
                
        messagebox.showinfo("جاري التفريغ", "تم حفظ التصنيفات بنجاح!\nيقوم النظام الآن بتجميع النص الكامل (Auto-Transcription)...\nيرجى مراجعة ملف output_text.txt")
        self.destroy()

if __name__ == "__main__":
    app = SpeechScribeGUI()
    app.mainloop()