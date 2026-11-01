"""Build a labelled contact sheet from preview stills: python3 src/contact.py out.png img1 img2 ..."""
import sys, cv2, numpy as np
out, files = sys.argv[1], sys.argv[2:]
tiles = []
for f in files:
    im = cv2.imread(f); im = cv2.resize(im, (270, 480), interpolation=cv2.INTER_AREA)
    cv2.putText(im, f.split('_')[-1][:-4], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    tiles.append(im)
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]
cv2.imwrite(out, np.vstack(rows))
