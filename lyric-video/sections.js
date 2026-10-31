// Структура песни (секунды). type задаёт палитру и силу эффектов.
window.SECTIONS = [
  { s: 0.0,   type: "intro"  },  // хук «Ты горишь как огонь»
  { s: 4.0,   type: "verse"  },  // куплет 1
  { s: 16.0,  type: "verse"  },  // брейк + перекличка артистов
  { s: 38.45, type: "chorus" },  // припев 1
  { s: 46.1,  type: "cold"   },  // куплет Газана (тише, холоднее)
  { s: 53.35, type: "drop"   },  // энергичный куплет
  { s: 69.0,  type: "freeze" },  // «всё вокруг замирает» — подводка
  { s: 73.95, type: "chorus" },  // припев 2
  { s: 81.2,  type: "break"  },
  { s: 83.35, type: "final"  },  // финальный припев
  { s: 97.8,  type: "outro"  },
];
window.TITLE = "ТЫ ГОРИШЬ\nКАК ОГОНЬ 2";
window.ARTISTS = "SLAVA MARLOW · GAZAN · КОБЯКОВ · TOLY SUMMER · ВОВА СОЛОДКОВ";
