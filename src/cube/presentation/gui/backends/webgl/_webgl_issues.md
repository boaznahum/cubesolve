1. no Crl C Alt C ✅
2. changing speed every thing is stuck ❌
2. Mouse control are all wrong, mouse cahnge view not rotating faces ✅
3. Face rotation:
   4. R ✅
   5. L ✅
   6. U ✅ 
   7. D ✅
   8. F ✅
   9. B ✅
   10. E ✅
   11. M ✅
   12. S ✅
   13. X ✅[claude-conversation-2026-02-27-f43f59ee.md](../../../../../../../Claude-Conversations/claude-conversation-2026-02-27-f43f59ee.md)
   14. Y ✅
   15. Z ✅
16. Slices are not animated.
17. The orange is yellow ✅
18. still happens Changing cube size, increase it view instead of fit it to current view ✅
19. code: e.keyCode, is deprected
20. Stop stop animation in the middle leaving face in undefined place, see pygelt2 how it handled correctly ✅
no
21. you insert a bug !!! during solver animation inner slices are naimated as whole silce ✅ 

22 Rotation on m slice on U and D are again in the wrong direction !!!

the queu it tool big, we can remove the indexing and put many algs in one line see https://cube-solver.com/#id=8

23. No central client state management. Client state is scattered across individual
    `send_*()` calls (send_speed, send_size, send_toolbar_state, send_cube_state,
    send_text, send_history_state, etc.). When state needs a full refresh (e.g.
    NewSessionCommand), we rely on `on_client_connected()` as a catch-all, but
    adding new state requires updating that method too. A proper solution would be
    a single state snapshot object that the client subscribes to, so any server-side
    change automatically syncs. Consider React or a centralized state store.
    Example: resize cube to 10x10, press Q (new session), nothing visually changes,
    scramble — still 10x10, press Q again — now shows 3x3. The scattered send calls
    mean some state updates are missed on the first reset.
